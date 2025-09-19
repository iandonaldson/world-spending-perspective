import typer
from cofogviz.coverage.build_coverage_registry import build_coverage_registry

def main():
    app = typer.Typer()

    @app.command()
    def build_coverage():
        """Build the coverage registry."""
        db_path = "local.duckdb"
        build_coverage_registry(db_path)
        print(f"Coverage registry built in {db_path}")

    app()