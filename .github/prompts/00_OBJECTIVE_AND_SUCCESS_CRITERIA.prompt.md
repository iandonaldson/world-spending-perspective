---
mode: agent
model: GPT-4o
tools: ['githubRepo','codebase','terminal']
description: 'Project objective, scope, and acceptance criteria for the COFOG drill-down ETL and viz system.'
---
# 00_OBJECTIVE_AND_SUCCESS_CRITERIA

> Feed this to GitHub Copilot Chat first. It sets scope, success criteria, and test checks for a drill‑down visualization of government spending by function using the COFOG classification, computed **as a percentage of revenue** (income) as well as other metrics.

---

## 1) End Objective (What we’re building)

Build a small, testable Python project that:
1. **Ingests** official government finance data for **EEA countries**, **Switzerland**, and the **United Kingdom** from international providers (Eurostat, OECD, IMF).
2. **Harmonizes** those data into a local analytics store (DuckDB + Parquet) keyed on the **COFOG hierarchy (L1–L3)** and **time (year)**, with provider provenance and metadata.
3. **Computes metrics** required for the visualization, especially **spending by function as a percentage of total government revenue** (income), and (optionally) % of total expenditure and % of GDP when available.
4. **Exposes a simple API/query layer** (to be added later) that returns tidy rows for `{geo, year, level}` to drive a drill‑down viz (L1→L2→L3), with clear indication when L3 is unavailable.
5. **Implements a provider fallback** so a requested `{geo, year, level}` is served from the best available source: **Eurostat → OECD → IMF** (EEA‑optimised), while keeping fallback order configurable. UK ≥ 2021 relies on **OECD/IMF**.

**Non‑Goals (for now):**
- Rich front‑end/UX (we focus on clean data + stable API first).
- Currency conversions, PPP adjustments, or synthetic disaggregation to L3.
- Non‑general‑government sectors (we focus on **S13**).

---

## 2) Background: Data & Standards (what Copilot should assume)

- **COFOG** (Classification of the Functions of Government): 3‑level international hierarchy (Divisions L1 → Groups L2 → Classes L3). We will version our canonical codelist and store multilingual labels.
- **Providers & datasets** (we will implement adapters):
  - **Eurostat**: `gov_10a_exp` (COFOG by function), plus totals for **revenue** and **expenditure** (S13). Best depth for EEA/CH; UK typically up to 2020.
  - **OECD**: `SNA_TABLE11` (COFOG by function) and national‑accounts totals; includes **UK** and non‑EU OECD members.
  - **IMF**: `GFS_COFOG` (COFOG by function) and GFS totals; broadest coverage; strongest at L1.
- **Units** we will persist: **amounts** (national currency and/or EUR if provided), **PC_TOT** (% of total government expenditure), and compute **% of revenue** using totals in the same year and sector (S13).
- **Assumptions confirmed by the user:**
  1) Include **Switzerland** and **UK** by default.
  2) Use **httpx** for HTTP.
  3) Default storage: **DuckDB + Parquet**, but abstract the warehouse so it can be swapped later.
  4) **Ingest all available years** per provider (don’t hard‑limit).
  5) Development in **GitHub Codespaces** with a minimal **devcontainer.json** and project‑local `venv` (Docker base kept minimal).

---

## 3) Success Criteria (Definition of Done)

### Functional
- **F1**: For any `{geo ∈ EEA ∪ {CH, UK}, year, level ∈ {1,2,3}}`, the system returns rows `{cofog_code, label, level, value}` for at least one metric where published (amounts or %), or a clear “not available” status when data are missing.
- **F2**: **% of revenue** is calculated from stored totals (same `{geo, year, sector=S13}`), not scraped from text.
- **F3**: Provider **fallback** works transparently and records the chosen provider + dataset + vintage timestamp on every row.
- **F4**: Aggregation checks hold: sum(L2) ≈ L1 when both are present (within configurable tolerance due to rounding/suppression).

### Data Quality & Provenance
- **DQ1**: Every record carries `provider`, `dataset_id`, `vintage_ts`, and `unit`.
- **DQ2**: COFOG labels are pulled from a **versioned canonical codelist**; no hard‑coded strings in business logic.
- **DQ3**: No synthetic L3 is generated when not published; L3 is optional and visibly flagged when absent.

### Performance & DevEx
- **P1**: Building the harmonized store for “EEA+CH+UK, all years” completes locally in a Codespace in a reasonable time (goal: under ~10 minutes on a warm cache; first run can be longer).
- **P2**: Responding to a typical query (`geo=NO, year=2023, level=2, metric=pct_of_revenue`) from the local API is sub‑second when cached (target < 300 ms).

### Maintainability
- **M1**: Clear repo structure; adapters and warehouse layers are isolated behind interfaces.
- **M2**: CI runs lint/type/unit tests; basic smoke tests validate provider routing and data integrity.
- **M3**: Minimal config via `.env` and `pyproject.toml`; reproducible in a fresh Codespace (`make bootstrap`).

---

## 4) User Stories (drive Copilot behavior)

- **US1 (Analyst):** As a policy analyst, I select a country (e.g., NO), year (e.g., 2023), and COFOG level (L2) to see each function’s **% of revenue**.
- **US2 (Researcher):** I can drill from L1→L2→L3 for a country/year and see which levels are available, with a clear indication when L3 is not published.
- **US3 (Compare):** I can compare L1 across multiple countries in a given year, switching metrics between **% of revenue**, **% of total expenditure**, and **amount**.
- **US4 (Traceability):** I can view provider provenance (Eurostat/OECD/IMF), dataset ID, and vintage date for any figure.
- **US5 (UK/Edge):** For UK 2021+, the system still serves valid results using OECD or IMF without manual reconfiguration.

---

## 5) Acceptance Tests (Copilot should help scaffold these)

> Copilot: generate tests or scripts to verify each item.

1. **Data Availability Matrix**: For a sample of countries across EEA, CH, UK and 3 years (e.g., 2015, 2020, latest), assert that at least L1 is returned; if L2/L3 exist per provider metadata, verify retrieval.
2. **% of Revenue Calculation**: For cases where amounts and totals exist, recompute `pct_of_revenue = amount / total_revenue * 100` and assert precision within tolerance (e.g., `±1e‑6`).
3. **Aggregation Integrity**: Where L1 & L2 are both present, assert `abs(sum(L2) - L1) / L1 < 0.01` (1% tolerance, configurable).
4. **Provider Fallback**: Temporarily disable Eurostat for `geo=IS` and assert that OECD/IMF is selected and provenance is stamped.
5. **UK Routing**: For UK 2022, assert provider chosen is OECD or IMF; for UK 2019, Eurostat may be acceptable.
6. **Metadata Completeness**: Assert every row has `provider`, `dataset_id`, `unit`, `vintage_ts`, and COFOG label resolved from the canonical codelist.
7. **Determinism**: Re‑run the same ingest on the same day (same provider vintage) and assert byte‑identical Parquet outputs (or checksum match).

---

## 6) Constraints & Guardrails for Copilot

- **No synthetic disaggregation to L3.**
- **No hard‑coding** of COFOG labels within business logic—always use the codelist.
- Keep **warehouse abstraction** clean (today: DuckDB; later: Postgres). Use a repository pattern or interface module for reads/writes.
- Prefer **httpx** for all HTTP calls; centralize timeouts/retries/backoff in a shared client.
- All ETL steps must be **idempotent** and tagged with `vintage_ts`.
- Keep Docker/devcontainer minimal; project‑local `venv` only.

---

## 7) Out‑of‑Scope / Future Work (for later prompt files)

- Domain deep‑dives via crosswalks (SHA↔COFOG 07 for health; ESSPROS↔COFOG 10 for pensions; CEPA/EPEA↔COFOG 05 for environment).
- GDP integration and currency conversions/PPP.
- Public deployment, auth, dashboards.

---

## 8) What Copilot should do next

1. Acknowledge objectives & constraints.
2. Confirm repo scaffolding strategy and test harness approach.
3. Prepare to consume **01_DATA_SOURCES_AND_STANDARDS.md** next and start drafting adapter interfaces and warehouse schema stubs accordingly.
4. Propose a minimal “hello world” script that pings providers and writes an empty, versioned codelist + an empty coverage registry (for CI smoke tests).

---

## 9) Testing Suggestions **before** proceeding

- Create a tiny **smoke test** that runs in CI: build a local DuckDB file, write an empty `dim_cofog` codelist (versioned), and ensure the process exits 0.
- Add a **connectivity probe** (with short timeouts) that calls each provider’s metadata endpoint and prints a concise coverage summary; skip on CI but document a local run.
- Pin a **test vintage** (e.g., today’s date) in a `.env` and ensure all outputs include it, enabling reproducible checksums in snapshot tests.
