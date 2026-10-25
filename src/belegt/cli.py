"""Command line entry point."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Annotated, Any

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
def extract(
    out: Annotated[Path, typer.Option(help="Directory for the source files")] = Path("data/raw"),
    work: Annotated[Path, typer.Option(help="Scratch space for the large downloads")] = Path(
        "data/downloads"
    ),
) -> None:
    """Download the full German source files (needs network; runs in GitHub Actions)."""
    from belegt.extract import extract_all

    for f in extract_all(out, work):
        rows = f"{f.rows} rows, " if f.rows is not None else ""
        typer.echo(f"{f.file}: {rows}{f.bytes:,} bytes, sha256 {f.sha256[:12]}")


@app.command()
def load(
    source: Annotated[Path, typer.Option(help="Directory with the source files")] = Path(
        "data/raw"
    ),
    db: Annotated[Path, typer.Option(help="DuckDB file")] = Path("data/belegt.duckdb"),
    bigquery_project: Annotated[
        str | None, typer.Option(help="Load into BigQuery dataset `raw` of this project instead")
    ] = None,
) -> None:
    """Parse the source files and replace the raw tables in DuckDB or BigQuery."""
    from belegt.warehouse import load_bigquery, load_directory

    if bigquery_project:
        counts = load_bigquery(source, bigquery_project)
    else:
        counts = load_directory(source, db)
    for table, n in counts.items():
        typer.echo(f"raw.{table}: {n} rows")


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


def _embedder(name: str) -> Any:
    from belegt.rag.embedding import E5Embedder, HashingEmbedder

    return E5Embedder() if name == "e5" else HashingEmbedder()


@app.command("rag-load")
def rag_load(
    project: Annotated[str, typer.Option(help="GCP project with the `rag` dataset")],
    chunks: Annotated[Path, typer.Option(help="JSON lines from `belegt index`")] = Path(
        "data/chunks.jsonl"
    ),
    embedder: Annotated[str, typer.Option(help="e5 (semantic) or hashing (tests)")] = "e5",
) -> None:
    """Embed the chunks, replace `rag.chunks` and (re)create one row access policy per tenant."""
    from google.cloud import bigquery

    from belegt.api.app import load_chunks
    from belegt.documents.model import SHARED_TENANT
    from belegt.rag.bigquery import (
        CHUNKS_TABLE,
        chunk_rows,
        row_access_policy_sql,
        tenant_service_account,
    )
    from belegt.rag.bigquery import load_chunks as load_table

    items = load_chunks(chunks)
    table = f"{project}.rag.{CHUNKS_TABLE}"
    client = bigquery.Client(project=project)
    n = load_table(client, table, chunk_rows(items, _embedder(embedder)))
    typer.echo(f"{table}: {n} chunks")
    for tenant in sorted({c.tenant_id for c in items} - {SHARED_TENANT}):
        member = f"serviceAccount:{tenant_service_account(tenant, project)}"
        client.query(row_access_policy_sql(table, tenant, member)).result()
        typer.echo(f"row access policy tenant_{tenant} -> {member}")


@app.command("rag-ask")
def rag_ask(
    question: str,
    tenant: Annotated[str, typer.Option(help="The tenant asking; queries run as its identity")],
    project: Annotated[str, typer.Option(help="GCP project with the `rag` dataset")],
    embedder: Annotated[str, typer.Option(help="e5 (semantic) or hashing (tests)")] = "e5",
) -> None:
    """Answer from BigQuery with citations, as JSON (used by the cloud evals)."""
    from belegt.rag.answer import Answerer
    from belegt.rag.bigquery import BigQueryRetriever, impersonating_client
    from belegt.rag.extractive import ExtractiveModel

    retriever = BigQueryRetriever(
        impersonating_client(project), f"{project}.rag", _embedder(embedder)
    )
    result = Answerer(retriever, ExtractiveModel(), min_score=0.1).ask(question, tenant)
    typer.echo(json.dumps(asdict(result), ensure_ascii=False))


@app.command("rag-eval")
def rag_eval(
    chunks: Annotated[Path, typer.Option(help="The corpus, as JSON lines")] = Path(
        "data/chunks.jsonl"
    ),
    cases: Annotated[Path, typer.Option(help="Evaluation cases")] = Path("evals/rag_cases.jsonl"),
    backend: Annotated[str, typer.Option(help="memory (offline) or bigquery")] = "memory",
    project: Annotated[str | None, typer.Option(help="GCP project for --backend bigquery")] = None,
    embedder: Annotated[str, typer.Option(help="e5 (semantic) or hashing (tests)")] = "hashing",
    out: Annotated[Path | None, typer.Option(help="Write the Markdown report here")] = None,
) -> None:
    """Run the evaluation cases; exits non-zero on any leak."""
    from belegt.api.app import load_chunks
    from belegt.rag.answer import Answerer
    from belegt.rag.evals import read_cases, report, run
    from belegt.rag.extractive import ExtractiveModel
    from belegt.rag.retrieval import InMemoryRetriever, Retriever

    corpus = load_chunks(chunks)
    owners = {c.doc_id: c.tenant_id for c in corpus}
    retriever: Retriever
    if backend == "bigquery":
        if not project:
            raise typer.BadParameter("--project is required for the bigquery backend")
        from belegt.rag.bigquery import BigQueryRetriever, impersonating_client

        retriever = BigQueryRetriever(
            impersonating_client(project), f"{project}.rag", _embedder(embedder)
        )
    else:
        retriever = InMemoryRetriever(_embedder(embedder), corpus)
    outcomes = run(read_cases(cases), Answerer(retriever, ExtractiveModel(), min_score=0.1), owners)
    text = report(outcomes, f"Document assistant evaluation ({backend}, {embedder})")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    typer.echo(text)
    if any(o.leaked for o in outcomes):
        raise typer.Exit(1)
