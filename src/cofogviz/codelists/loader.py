import duckdb
import pyarrow as pa
import pyarrow.parquet as pq
from datetime import datetime
import os

def write_empty_cofog_codelist(db_path: str, vintage_ts: str):
    table = pa.table({
        "cofog_code": pa.array([], pa.string()),
        "label": pa.array([], pa.string()),
        "level": pa.array([], pa.int8())
    })
    pq.write_table(table, "CL_COFOG.parquet")
    con = duckdb.connect(db_path)
    con.execute("CREATE TABLE IF NOT EXISTS dim_cofog (cofog_code VARCHAR, label VARCHAR, level TINYINT, vintage_ts VARCHAR)")
    con.close()