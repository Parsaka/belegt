"""Command line entry point."""

from __future__ import annotations

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
