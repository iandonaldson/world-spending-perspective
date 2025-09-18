---
mode: agent
model: GPT-4o
tools: ['githubRepo','codebase','terminal']
description: 'Authoritative data sources, APIs, formats, and standards for COFOG drill-down ETL with testing suggestions.'
---

# 01_DATA_SOURCES_AND_STANDARDS

> Purpose: Give Copilot an authoritative, implementation-ready brief on **where** data come from, **how** to query them, **what** standards to respect (COFOG, SDMX, JSON-stat), and **what to test** before building adapters.

This project ingests **function-of-government** expenditure data (COFOG L1–L3 where available) and **totals** (revenue/expenditure for S13) for **EEA countries**, **Switzerland**, and the **United Kingdom**. We will store **amounts** and **shares** and compute **% of revenue**.

---

## 1) Core standards

- **COFOG** (Classification of the Functions of Government): hierarchical 3-level functional classification
  - L1 (Divisions, GF01..GF10), L2 (Groups, e.g., GF1001..), L3 (Classes).
  - Maintain a **canonical, versioned codelist** (multilingual labels) under `warehouse/codelists/CL_COFOG.parquet`.
- **S13**: General government sector (we restrict to S13).
- **Data formats** we will consume:
  - **JSON-stat 2.0** (Eurostat Statistics API).
  - **SDMX-JSON 2.1/3.0** (OECD, IMF, Eurostat SDMX if needed).

---

## 2) Primary providers & datasets (with example filters)

### Eurostat (preferred for EEA + CH depth)
- **COFOG by function**: dataset `gov_10a_exp` via **Statistics API (JSON-stat 2.0)**  
  Example filters:
  - `geo=<ISO-like code>` (e.g., `FR`, `NO`, `IS`, `CH`)
  - `time=<year>`
  - `unit ∈ {PC_TOT, MIO_EUR, MIO_NAC}`
  - `sector=S13`
  - `na_item=TE` (total expenditure)
  - `cofog99` contains L1/L2/L3 codes (request full dimension; downshift if not provided).
- **Totals (for % of revenue)**: pick an official Eurostat totals dataset for **general government revenue/expenditure** (S13). We will store both `total_revenue` and `total_expenditure` per `{geo, year, unit}`.

> Notes
- UK data in Eurostat generally end by **2020**; for 2021+ use OECD/IMF.
- JSON-stat responses include dimension metadata and sparse values; we’ll parse via `pyjstat` where possible and implement a minimal fallback parser.

### OECD (extends coverage beyond EU; includes UK)
- **COFOG by function**: SNA **Table 11** via **SDMX-JSON** (`SNA_TABLE11`).
- **Totals**: OECD National Accounts series (general government revenue/expenditure).

> Notes
- Structure and codelists are SDMX; we’ll use `pandaSDMX` and normalize dimension IDs to our canonical schema.

### IMF (broadest global coverage; strongest at L1)
- **COFOG by function**: **GFS_COFOG** via **SDMX-JSON**.
- **Totals**: GFS aggregates for **general government revenue/expenditure**.

> Notes
- Expect L1 everywhere; L2/L3 vary by country/year. Use the **coverage registry** to choose level per request.

---

## 3) Coverage & routing policy (for adapters)

- **Default routing (EEA-optimised)**: **Eurostat → OECD → IMF**.
- **Requested alternative (supported via config)**: **IMF → OECD → Eurostat**.
- **UK (>=2021)**: prefer **OECD**, fallback **IMF**; <=2020 can use Eurostat when available.
- Implement a **coverage registry** refreshed weekly: for each `{provider, geo}` record `min_year`, `max_year`, `max_level`, `units_available`.

---

## 4) Dimensions, units, and integrity

- Dimensions to standardize: `geo`, `time` (year), `cofog_code`, `cofog_level`, `sector` (S13), `unit`, `provider`, `dataset_id`, `vintage_ts`.
- **Units to persist**:
  - **Amounts**: `MIO_EUR` and/or `MIO_NAC` (national currency) when provided.
  - **Shares**: `PC_TOT` (% of **total expenditure**).
  - Derived metric: **`pct_of_revenue`** = `amount / total_revenue_amount * 100` for the same `{geo, year, S13, unit}`.
- **Integrity checks**:
  - If both L1 and L2 exist, assert `Σ(L2) ≈ L1` within tolerance (rounding/suppression).
  - Never synthesize L3—only store published classes.

---

## 5) HTTP & reliability (shared client)

- Use **httpx** with:
  - timeouts, retries with exponential backoff, jitter,
  - User-Agent with project/version,
  - structured logging and request IDs.
- Handle provider-specific rate limits politely; cache responses on disk (ETag/Last-Modified if supported).

---

## 6) Adapter interface and parsing (what to implement)

Create a small interface contract and provider-specific implementations.

```python
# src/adapters/base.py
from dataclasses import dataclass
from typing import Iterable, Literal, Optional

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

    async def capabilities(self, geo: str) -> ProviderCaps:
        """Probe metadata for {geo}: year span, highest COFOG level, units."""

    async def fetch_functions(self, geo: str, year: int, level: Level) -> Iterable[dict]:
        """Yield records with keys: geo, year, cofog_code, level, unit, value, provider, dataset_id, vintage_ts."""

    async def fetch_totals(self, geo: str, year: int) -> Iterable[dict]:
        """Yield totals for general government revenue/expenditure for S13 in all available units."""
```

Eurostat JSON-stat parsing helper:

```python
# src/adapters/jsonstat_utils.py
from collections.abc import Mapping
def parse_jsonstat_dataset(obj: Mapping) -> list[dict]:
    """Return tidy rows with dimension keys and value. Handle sparse 'value' dicts."""
    ...
```

SDMX parsing approach (OECD/IMF):

```python
# src/adapters/sdmx_utils.py
from pandasdmx import Request  # optional; otherwise parse SDMX-JSON directly
def sdmx_to_rows(sdmx_json: dict) -> list[dict]:
    """Normalize SDMX-JSON structure to tidy rows."""
    ...
```

---

## 7) Totals (for % of revenue)

For each provider, identify and ingest the **general government (S13)** totals for:
- `total_revenue` and `total_expenditure`,
- in all units provided (national currency, EUR where available).

Store them in `fact_gov_totals` and compute `pct_of_revenue` during **gold publish**.

---

## 8) Provenance & metadata

Every row (functions & totals) must include:
- `provider` (EUROSTAT | OECD | IMF),
- `dataset_id`,
- `unit`,
- `vintage_ts` (UTC timestamp of ingestion run),
- optional `obs_status/flags` from the source.

Keep dataset pages/links in code comments; do not hard-code labels—resolve via codelists.

---

## 9) Testing suggestions (run before building full ETL)

Copilot: scaffold these tests.

1. **Connectivity probes** (skippable on CI): try one metadata call per provider; assert 200 OK; log year span & max level for `{FR, NO, IS, CH, UK}`.
2. **Shape tests** (unit): Given a small canned response (JSON-stat and SDMX-JSON fixtures), assert parsers return tidy rows with required keys.
3. **Integrity check** (unit): Given mocked L1 & L2 rows, assert Σ(L2) ≈ L1 within tolerance.
4. **Totals join** (unit): Join a sample function amount with totals and assert `pct_of_revenue` precision.
5. **Routing smoke** (integration): With a tiny coverage registry (e.g., Eurostat disabled for `IS`), assert that OECD/IMF is chosen and provenance is stamped.
6. **Idempotency/snapshot** (integration): Run the same ingest twice with a fixed `vintage_ts`; assert identical Parquet checksums.

---

## 10) Instructions to Copilot (what to generate next)

- Create the **adapter interfaces** and **shared httpx client** with retry/backoff.
- Add **minimal Eurostat adapter** that can:
  - fetch `gov_10a_exp` for given `{geo, year}`, returning L1/L2 present in the response;
  - fetch general-government totals (revenue/expenditure) for the same `{geo, year}`;
  - parse via `pyjstat`, fallback to a small in-house parser.
- Add stubs for **OECD** and **IMF** adapters that currently just expose `capabilities()` returning placeholders (to be filled later).
- Write unit tests for the two parsing helpers (JSON-stat, SDMX-JSON) using small fixtures in `tests/fixtures/`.
- Do **not** wire the warehouse yet; we’ll define schema next. Aim to return tidy rows and log comprehensive metadata.
