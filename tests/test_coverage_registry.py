import duckdb
from cofogviz.coverage.build_coverage_registry import build_coverage_registry

def test_build_coverage_registry():
    db_path = "test.duckdb"
    build_coverage_registry(db_path)

    con = duckdb.connect(db_path)
    rows = con.execute("SELECT * FROM coverage_registry").fetchall()
    assert len(rows) > 0
    con.close()