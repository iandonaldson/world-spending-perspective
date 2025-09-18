import duckdb
from datetime import datetime
from typing import Dict, List, Tuple
from src.routing.choose_source import ProviderCaps

def mock_provider_capabilities() -> Dict[Tuple[str, str], ProviderCaps]:
    return {
        ("EUROSTAT", "NO"): ProviderCaps(min_year=2000, max_year=2023, max_level=3, units=["MIO_EUR", "PC_TOT"]),
        ("OECD", "NO"): ProviderCaps(min_year=1995, max_year=2023, max_level=2, units=["MIO_NAC"]),
        ("IMF", "NO"): ProviderCaps(min_year=1980, max_year=2023, max_level=1, units=["MIO_NAC"]),
    }

def build_coverage_registry(db_path: str):
    coverage = mock_provider_capabilities()
    con = duckdb.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS coverage_registry (
            provider VARCHAR,
            geo VARCHAR,
            min_year INT,
            max_year INT,
            max_level TINYINT,
            units VARCHAR,
            updated_at TIMESTAMP
        )
    """)

    for (provider, geo), caps in coverage.items():
        con.execute(
            "INSERT INTO coverage_registry VALUES (?, ?, ?, ?, ?, ?, ?)",
            (provider, geo, caps.min_year, caps.max_year, caps.max_level, ",".join(caps.units), datetime.utcnow())
        )

    con.close()