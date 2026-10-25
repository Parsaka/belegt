"""Command line entry point."""

from __future__ import annotations

import json
from dataclasses import asdict
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
def index(
    pdf: Path,
    doc_id: Annotated[str, typer.Option(help="Stable id, e.g. basf-2024")],
    tenant: Annotated[
        str, typer.Option(help="Owner tenant; public reports are 'shared'")
    ] = "shared",
    out: Annotated[Path, typer.Option(help="JSON lines file to update")] = Path(
        "data/chunks.jsonl"
    ),
) -> None:
    """Chunk a PDF page by page into JSON lines for retrieval. The PDF itself stays local."""
    from belegt.documents.chunking import chunk_pages
    from belegt.documents.pdf import read_pages

    out.parent.mkdir(parents=True, exist_ok=True)
    existing = out.read_text().splitlines() if out.exists() else []
    kept = [line for line in existing if json.loads(line)["doc_id"] != doc_id]  # re-runs replace
    pages = read_pages(pdf, doc_id)
    chunks = [json.dumps(asdict(c), ensure_ascii=False) for c in chunk_pages(pages, tenant)]
    out.write_text("\n".join([*kept, *chunks]) + "\n")
    typer.echo(f"{doc_id}: {len(chunks)} chunks -> {out}")
