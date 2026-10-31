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
    title: Annotated[
        str | None, typer.Option(help="Document title, embedded with every chunk")
    ] = None,
    pages_matching: Annotated[
        str | None,
        typer.Option(help="Index only pages whose text matches this regular expression"),
    ] = None,
) -> None:
    """Chunk a PDF page by page into JSON lines for retrieval. The PDF itself stays local."""
    import re

    from belegt.documents.chunking import chunk_pages
    from belegt.documents.pdf import read_pages

    out.parent.mkdir(parents=True, exist_ok=True)
    existing = out.read_text().splitlines() if out.exists() else []
    kept = [line for line in existing if json.loads(line)["doc_id"] != doc_id]  # re-runs replace
    pages = read_pages(pdf, doc_id)
    if pages_matching:
        wanted = re.compile(pages_matching, re.I)
        pages = (p for p in pages if wanted.search(p.text))
    chunks = [
        json.dumps(asdict(c), ensure_ascii=False) for c in chunk_pages(pages, tenant, title=title)
    ]
    out.write_text("\n".join([*kept, *chunks]) + "\n")
    typer.echo(f"{doc_id}: {len(chunks)} chunks -> {out}")


REPORT_SEED = Path("dbt/seeds/reports.csv")


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
    from belegt.rag.names import ReportNames

    retriever = BigQueryRetriever(
        impersonating_client(project), f"{project}.rag", _embedder(embedder)
    )
    names = ReportNames.from_seed(REPORT_SEED)
    model = ExtractiveModel(names.words)
    result = Answerer(retriever, model, min_score=0.1, names=names).ask(question, tenant)
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
    from belegt.rag.names import ReportNames
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
    names = ReportNames.from_seed(REPORT_SEED)
    answerer = Answerer(retriever, ExtractiveModel(names.words), min_score=0.1, names=names)
    outcomes = run(read_cases(cases), answerer, owners)
    text = report(outcomes, f"Document assistant evaluation ({backend}, {embedder})")
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    typer.echo(text)
    if any(o.leaked for o in outcomes):
        raise typer.Exit(1)


@app.command()
def reports(
    seed: Annotated[Path, typer.Option(help="The report list")] = Path("dbt/seeds/reports.csv"),
    index: Annotated[
        int | None,
        typer.Option(help="Process this row only; default: the job's task index, else every row"),
    ] = None,
    out: Annotated[
        str, typer.Option(help="Directory or gs:// prefix for metrics/<doc_id>.jsonl")
    ] = "data/raw/reports",
    pdf_out: Annotated[
        str | None, typer.Option(help="Private directory or gs:// prefix for the PDFs themselves")
    ] = None,
    work: Annotated[Path, typer.Option(help="Scratch space for the download")] = Path(
        "data/downloads/reports"
    ),
) -> None:
    """Download sustainability statements and extract Scope 1-3 totals with page citations.

    Prints one JSON line per report. In a job (one report per task) a failure exits non-zero so
    the scheduler retries that task; over every row, failures are reported and the rest go on.
    """
    import httpx

    from belegt.documents.reports import process, read_seed, sink_for, task_index
    from belegt.extract import USER_AGENT

    rows = read_seed(seed)
    position = index if index is not None else task_index()
    todo = [rows[position]] if position is not None else rows
    sink = sink_for(out)
    pdf_sink = sink_for(pdf_out) if pdf_out else None
    failed = 0
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=300, follow_redirects=True
    ) as client:
        for report in todo:
            try:
                result = process(report, client, work, sink, pdf_sink)
            except Exception as error:  # one bad host must not hide the other reports
                failed += 1
                typer.echo(json.dumps({"doc_id": report.doc_id, "error": str(error)[:300]}))
                continue
            typer.echo(json.dumps(asdict(result)))
    if failed and (position is not None or failed == len(todo)):
        raise typer.Exit(1)


@app.command("reports-eval")
def reports_eval(
    metrics: Annotated[Path, typer.Argument(help="Directory with metrics/<doc_id>.jsonl")],
    labels: Annotated[Path, typer.Option(help="Hand-labelled values")] = Path(
        "evals/reported_metrics.csv"
    ),
    out: Annotated[Path | None, typer.Option(help="Write the Markdown report here")] = None,
) -> None:
    """Score the extracted Scope 1-3 figures against the hand labels, per metric and split."""
    from belegt.documents.evaluation import evaluate, read_labels, read_selected, report

    files = sorted(metrics.glob("*.jsonl"))
    selected = read_selected(line for f in files for line in f.read_text().splitlines())
    outcomes = evaluate(read_labels(labels), selected, {f.stem for f in files})
    text = report(outcomes)
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text)
    typer.echo(text)


# Pages of a report that the document assistant indexes: the climate disclosures, not the
# whole annual report
CLIMATE_PAGES = (
    r"\bScope[\s-]*[123]\b|greenhouse gas|Treibhausgas|\bGHG\b|\bTHG\b|E1-\d|"
    r"climate|Klima|CO2|CO₂"
)


@app.command("index-reports")
def index_reports(
    pdf_dir: Annotated[Path, typer.Argument(help="Directory with <doc_id>.pdf")],
    corpus: Annotated[Path, typer.Option(help="doc_id,tenant: who may read which report")] = Path(
        "evals/rag_corpus.csv"
    ),
    seed: Annotated[Path, typer.Option(help="The report list, for titles")] = Path(
        "dbt/seeds/reports.csv"
    ),
    out: Annotated[Path, typer.Option(help="JSON lines file to update")] = Path(
        "data/chunks.jsonl"
    ),
) -> None:
    """Chunk the climate pages of every report in the corpus, each owned by one tenant."""
    import csv
    import re

    from belegt.documents.chunking import chunk_pages
    from belegt.documents.pdf import read_pages
    from belegt.documents.reports import read_seed

    reports = {r.doc_id: r for r in read_seed(seed)}
    with corpus.open(newline="", encoding="utf-8") as fh:
        owners = {row["doc_id"]: row["tenant"] for row in csv.DictReader(fh)}
    unknown = set(owners) - set(reports)
    if unknown:
        raise typer.BadParameter(f"not in the report seed: {sorted(unknown)}")
    wanted = re.compile(CLIMATE_PAGES, re.I)
    out.parent.mkdir(parents=True, exist_ok=True)
    existing = out.read_text().splitlines() if out.exists() else []
    kept = [line for line in existing if json.loads(line)["doc_id"] not in owners]
    lines: list[str] = []
    for doc_id, tenant in owners.items():
        pdf = pdf_dir / f"{doc_id}.pdf"
        if not pdf.exists():
            typer.echo(f"{doc_id}: no PDF, skipped")
            continue
        report = reports[doc_id]
        title = f"{report.company}, report {report.report_year}"
        pages = (p for p in read_pages(pdf, doc_id) if wanted.search(p.text))
        chunks = list(chunk_pages(pages, tenant, title=title))
        lines += [json.dumps(asdict(c), ensure_ascii=False) for c in chunks]
        typer.echo(f"{doc_id}: {len(chunks)} chunks for {tenant}")
    out.write_text("\n".join([*kept, *lines]) + "\n")
