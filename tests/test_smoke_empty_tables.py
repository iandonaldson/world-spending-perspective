import duckdb
import os

def test_empty_tables_exist():
    db_path = "local.duckdb"
    con = duckdb.connect(db_path)
    tables = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
    assert "dim_cofog" in tables
    assert "coverage_registry" in tables
    con.close()
