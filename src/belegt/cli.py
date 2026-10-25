"""Command line entry point."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from belegt.sources import SOURCES

app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.callback()
def main() -> None:
    """Belegt: ESG data with every number traceable to its source."""


@app.command()
def sources() -> None:
    """List the registered data sources, their licences and open questions."""
    for source in SOURCES:
        typer.echo(f"{source.id}  [{source.verification}]")
        typer.echo(f"  {source.name} ({source.publisher})")
        typer.echo(f"  licence: {source.licence}")
        if source.open_question:
            typer.echo(f"  open: {source.open_question}")


@app.command()
def load(
    source: Annotated[Path, typer.Option(help="Directory with the source files")] = Path(
        "data/raw"
    ),
    db: Annotated[Path, typer.Option(help="DuckDB file")] = Path("data/belegt.duckdb"),
) -> None:
    """Parse the source files and replace the raw tables in DuckDB."""
    from belegt.warehouse import load_directory

    for table, n in load_directory(source, db).items():
        typer.echo(f"raw.{table}: {n} rows")
