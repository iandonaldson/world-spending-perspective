---
mode: agent
model: GPT-4o
tools: ['githubRepo','codebase','terminal']
description: 'System architecture, routing/fallback logic, coverage registry, and reliability patterns for the COFOG drill-down ETL.'
---

# 02_SYSTEM_ARCHITECTURE_AND_ROUTING

> Purpose: Define the end-to-end system, provider routing/fallback, the **coverage registry**, and reliability/observability. Keep this infra-focused. We’ll define data model tables in **03_DATA_MODEL_AND_SCHEMA**.

The user has confirmed:
- Include **EEA countries**, **Switzerland**, and **United Kingdom** by default.
- Use **httpx** with centralized retry/backoff.
- Default store is **DuckDB + Parquet** but keep the persistence layer **abstract** (swap-able later).
- **Ingest all available years** per provider.
- Minimal **devcontainer + local venv**; grow as needed.

---

## 1) High-level architecture (Bronze → Silver → Gold)

```
[Providers: Eurostat | OECD | IMF]
      │
      ▼
[Adapters]  (httpx client + parsers)
      │                 ┌──────────┐
      ├──► [Bronze] ───►│ Raw dump │  (JSON-stat / SDMX-JSON snapshots, optional)
      │                 └──────────┘
      ▼
[Normalizer] → standard tidy rows (functions, totals) + provenance
      │
      ├──► [Silver] (harmonized facts & dims; no business calc yet)
      │
      └──► [Gold]   (analytics-ready: % of revenue, % of expenditure, amounts)
                           │
                           ▼
                     [Viz/API service]
```

**Key components**
- **Adapters**: Eurostat (JSON-stat), OECD (SDMX-JSON), IMF (SDMX-JSON) behind a common interface.
- **Coverage Registry**: precomputed capabilities for `{provider, geo}` → `{min_year, max_year, max_level, units}`.
- **Warehouse Abstraction**: simple repository layer (`warehouse/`) with interchangeable backend (start with DuckDB).
- **Jobs**: `build_coverage_registry`, `ingest_functions`, `ingest_totals`, `normalize_to_silver`, `publish_gold`.
- **Codelists**: versioned **COFOG** codelist (L1–L3) stored once and referenced everywhere.

---

## 2) Routing & fallback (country/year/level)

Two configurable presets:
- **Preset A (EEA-optimised default):** `EUROSTAT → OECD → IMF`
- **Preset B (requested alternative):** `IMF → OECD → EUROSTAT`

**UK rule**:
- `year >= 2021` → prefer **OECD**, fallback **IMF**
- `year <= 2020` → Eurostat acceptable if present

### Selection algorithm (pseudocode)

```python
def choose_source(geo, year, desired_level, order):
    # Special-case UK routing
    if geo == "UK" or geo == "GB" or geo == "GBR":
        if year >= 2021:
            order = ["OECD", "IMF", "EUROSTAT"]

    for provider in order:
        caps = coverage[(provider, geo)]  # ProviderCaps(min_year, max_year, max_level, units)
        if caps and caps.min_year <= year <= caps.max_year:
            level = min(desired_level, caps.max_level)
            if level is not None:
                return provider, level
    raise NoDataError(f"No provider for {geo} {year} at level {desired_level}")
```

**Level handling**
- Request **desired level**; if unavailable, **downshift** (L3→L2→L1) according to `max_level`.
- Always record the **actual level served** and the **provider** in provenance.

**Units**
- Prefer **amounts** (MIO_EUR or MIO_NAC) when available.
- Persist **PC_TOT** (share of expenditure) if published.
- Compute **pct_of_revenue** during Gold publish using totals for the same `{geo, year, S13}`.

---

## 3) Coverage Registry

Purpose: Avoid runtime guesswork. Precompute per `{provider, geo}`:
- `min_year`, `max_year`
- `max_level` (1/2/3)
- `units` (e.g., `["MIO_NAC", "MIO_EUR", "PC_TOT"]`)
- `updated_at` (UTC)
- optional `notes` (e.g., “UK after 2020 not maintained in Eurostat”)

**Builder job** (`src/coverage/build_coverage_registry.py`):
- Uses lightweight metadata calls (or a shallow data probe) to infer coverage.
- Writes a Parquet (and/or DuckDB) table `coverage_registry`.
- **Schedule**: weekly; store vintages.

**Usage**:
- All ingest jobs consult the registry to pick the provider & level before fetching.
- The API layer exposes a `/metadata/coverage` endpoint for transparency.

---

## 4) Adapters & shared HTTP client

**Shared client** (`src/adapters/http.py`):
- `httpx.AsyncClient` with:
  - timeouts, retry with exponential backoff + jitter
  - per-host rate limits
  - default headers (User-Agent with repo/version)
  - structured logging (request id, status, duration)

**Adapter interface** (`src/adapters/base.py`):
```python
from dataclasses import dataclass
from typing import Iterable, Literal

Level = Literal[1, 2, 3]

@dataclass(frozen=True)
class ProviderCaps:
    min_year: int
    max_year: int
    max_level: Level
    units: list[str]

class ProviderAdapter:
    name: str
    dataset_id_functions: str
    dataset_id_totals: str

    async def capabilities(self, geo: str) -> ProviderCaps: ...
    async def fetch_functions(self, geo: str, year: int, level: Level) -> Iterable[dict]: ...
    async def fetch_totals(self, geo: str, year: int) -> Iterable[dict]: ...
```

**Eurostat/OECD/IMF adapters** live in `src/adapters/` and should:
- Return **tidy rows** with keys:
  `geo, year, cofog_code, level, unit, value, provider, dataset_id, vintage_ts[, obs_status, flags]`
- Never synthesize L3; only return published data.

---

## 5) Warehouse abstraction

Create a minimal repository layer so backends are swappable:
- `warehouse/base.py` → interfaces for `write_dim_cofog`, `write_coverage_registry`, `append_functions_raw`, `append_totals_raw`, `upsert_silver`, `publish_gold`.
- `warehouse/duckdb_repo.py` → default implementation.
- Later you can add `warehouse/postgres_repo.py`.

**Idempotency & keys**
- Use deterministic keys:
  - functions: `(geo, year, cofog_code, unit, provider, vintage_ts)`
  - totals: `(geo, year, measure, unit, provider, vintage_ts)`
- Writes should be upserts keyed on these fields.

---

## 6) Jobs (CLI tasks)

Implement with `typer` for a simple CLI:

- `build_coverage_registry` → refresh capabilities for `{EEA, CH, UK}`
- `ingest_functions --geo --year --level` → fetch & persist
- `ingest_totals --geo --year` → fetch & persist revenue/expenditure totals
- `normalize_to_silver --geo --year` → harmonize raw rows → silver
- `publish_gold --geo --year` → compute `pct_of_revenue`, `pct_of_expenditure`, materialize gold
- `reindex_codelists` → load/refresh COFOG codelist (versioned)

`Makefile` targets:
```
make bootstrap
make coverage
make ingest GEO=NO YEAR=2023 LEVEL=2
make publish GEO=NO YEAR=2023
make test
```

---

## 7) Reliability & observability

- **Retries/backoff** in HTTP client; honor provider rate limits.
- **Structured logging** (JSON): include request_id, geo, year, provider, level, unit, counts.
- **Metrics**: counters for rows ingested, providers chosen, fallback occurrences, errors.
- **Dead-letter**: on parse failure for a page/year, write a small raw dump to `logs/errors/…` for inspection.
- **Idempotency**: reruns with same `vintage_ts` produce identical outputs; new runs create new vintages.

---

## 8) Error handling & edge cases

- Missing L3: downshift to L2/L1; stamp `level_observed`.
- Partial years / embargoes: keep `obs_status` and `flags`.
- Unit gaps: if amounts missing but PC_TOT present, publish `% of expenditure` and mark `% of revenue` as unavailable.
- UK after 2020: route to OECD/IMF automatically.

---

## 9) Configuration (.env)

- `COUNTRY_SET=EEA,CH,UK` (expanded at runtime)
- `PROVIDER_ORDER=EUROSTAT,OECD,IMF` (override: IMF,OECD,EUROSTAT)
- `DUCKDB_PATH=.data/warehouse.duckdb`
- `PARQUET_ROOT=.data/parquet/`
- `HTTP_TIMEOUT_S=30`
- `HTTP_MAX_RETRIES=3`
- `HTTP_BACKOFF_BASE_MS=200`
- `CACHE_DIR=.cache/providers/`
- `VINTAGE_TS=auto`  (or ISO timestamp)
- `LOG_LEVEL=INFO`

---

## 10) Testing suggestions (run before schema work in 03)

Copilot: scaffold these tests.

**Unit**
1. **Routing logic**: Given a mock coverage registry and desired levels, assert provider/level selection for:
   - `NO, 2023, L2` → Eurostat
   - `IS, 2018, L1` → Eurostat or OECD depending on mock caps
   - `UK, 2022, L2` → OECD (IMF fallback)
2. **HTTP client**: Retry/backoff called as expected on 429/5xx; timeout respected.

**Integration (local)**
3. **Coverage registry build**: With mocked provider metadata, produce a registry for `{FR, NO, IS, CH, UK}` and assert fields set.
4. **Hello world ETL**: Runs end-to-end and creates empty `dim_cofog` + `coverage_registry`, both stamped with `vintage_ts`.

**Determinism**
5. Run `hello` twice with the same `VINTAGE_TS` and assert byte-identical Parquet/DB content.

**Observability**
6. Log lines include `provider`, `geo`, `year`, `level`, `duration_ms`, and counts of rows.

---

## 11) Instructions to Copilot (what to generate now)

- Create `src/routing/choose_source.py` implementing the selection algorithm using the coverage registry (in-memory and DuckDB-backed versions).
- Flesh out `src/coverage/build_coverage_registry.py` to **mock** capabilities (until adapters are ready), writing a real table.
- Implement `src/adapters/http.py` with async `httpx` client, retries/backoff, and structured logging.
- Add `src/cli.py` (Typer) wiring `build_coverage_registry`, `hello`.
- Update `Makefile` targets and `ci.yml` to run the integration smoke test.

> Do not define the Silver/Gold schemas yet; that comes in **03_DATA_MODEL_AND_SCHEMA**.
