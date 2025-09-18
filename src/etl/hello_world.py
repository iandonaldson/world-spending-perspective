
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.codelists.loader import write_empty_cofog_codelist
from src.coverage.registry import write_empty_coverage_registry

def main():
    load_dotenv()
    vintage_ts = os.getenv("VINTAGE_TS", datetime.now().isoformat())
    db_path = "local.duckdb"
    write_empty_cofog_codelist(db_path, vintage_ts)
    write_empty_coverage_registry(db_path, vintage_ts)
    print(f"Created DuckDB at {db_path} with vintage_ts={vintage_ts}")

if __name__ == "__main__":
    main()
