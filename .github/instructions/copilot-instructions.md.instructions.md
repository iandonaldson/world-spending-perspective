---
applyTo: '**'
---
Use httpx for HTTP (retry/backoff centralized).

Default warehouse is DuckDB + Parquet; keep the persistence layer abstracted (swap-able).

Never synthesize COFOG L3; only store L3 when published.

Always retain provenance (provider, dataset_id, unit, vintage_ts).

Compute % of revenue from totals (same {geo, year, S13}); don’t guess.

ETL must be idempotent and include integrity checks (ΣL2≈L1 within tolerance).

Keep Docker/devcontainer minimal; project-local venv only.