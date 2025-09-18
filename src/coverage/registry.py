import duckdb
from datetime import datetime

def write_empty_coverage_registry(db_path: str, vintage_ts: str):
    con = duckdb.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS coverage_registry (vintage_ts VARCHAR)")
    con.close()
