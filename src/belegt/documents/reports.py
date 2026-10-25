"""Sustainability statements: download one report and extract its greenhouse-gas totals.

One report is one unit of work, addressed by its row in `dbt/seeds/reports.csv`. The same
contract runs as a Kubernetes Indexed Job during the trial (`JOB_COMPLETION_INDEX`) and as a
Cloud Run job afterwards (`CLOUD_RUN_TASK_INDEX`), so the work is parallel without a queue.

Reports are copyrighted. The PDF goes only to the private reports bucket (or a local `data/`
directory); what leaves a task is the extracted figures with their page and table line.
Outputs are named after the report id, so a re-run overwrites them.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol

from belegt.documents import metrics

MAX_BYTES = 100 * 1024 * 1024  # an annual report with the sustainability statement is 5-40 MB
INDEX_VARIABLES = ("JOB_COMPLETION_INDEX", "CLOUD_RUN_TASK_INDEX")


class ReportError(RuntimeError):
    pass


@dataclass(frozen=True)
class Report:
    doc_id: str
    company: str
    lei: str
    report_year: int
    fiscal_year_end: str  # MM-DD
    language: str
    url: str
    host_note: str

    @property
    def decimal_comma(self) -> bool:
        return self.language == "de"


@dataclass(frozen=True)
class Result:
    doc_id: str
    bytes: int
    sha256: str
    pages: int
    candidates: int
    selected: dict[str, float]  # metric -> tonnes


def read_seed(path: Path) -> list[Report]:
    with path.open(newline="", encoding="utf-8") as fh:
        return [
            Report(**{**row, "report_year": int(row["report_year"])})  # type: ignore[arg-type]
            for row in csv.DictReader(fh)
        ]


def task_index(env: Mapping[str, str] = os.environ) -> int | None:
    """The task's position in the seed, from Kubernetes or Cloud Run; None outside a job."""
    for name in INDEX_VARIABLES:
        if env.get(name, "") != "":
            return int(env[name])
    return None


def download(client: Any, url: str, path: Path) -> tuple[int, str]:
    """Stream to `path`; (bytes, sha256). Refuses anything that is not a PDF or is too large."""
    digest = hashlib.sha256()
    size = 0
    with client.stream("GET", url) as response:
        response.raise_for_status()
        with path.open("wb") as fh:
            for chunk in response.iter_bytes(1 << 20):
                if size == 0 and not chunk.startswith(b"%PDF-"):
                    kind = response.headers.get("content-type", "unknown type")
                    raise ReportError(
                        f"{url} did not return a PDF ({kind}, final URL {response.url})"
                    )
                size += len(chunk)
                if size > MAX_BYTES:
                    raise ReportError(f"{url} is larger than {MAX_BYTES} bytes")
                digest.update(chunk)
                fh.write(chunk)
    if size == 0:
        raise ReportError(f"{url} returned an empty body")
    return size, digest.hexdigest()


def metrics_jsonl(found: Iterable[metrics.ReportedMetric]) -> bytes:
    return "".join(json.dumps(asdict(m), ensure_ascii=False) + "\n" for m in found).encode()


class Sink(Protocol):
    def put(self, name: str, data: bytes | Path, content_type: str) -> str: ...


class LocalSink:
    def __init__(self, root: Path) -> None:
        self.root = root

    def put(self, name: str, data: bytes | Path, content_type: str) -> str:
        target = self.root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data.read_bytes() if isinstance(data, Path) else data)
        return str(target)


class GcsSink:
    """A bucket prefix, written with the workload identity of the pod or job (no key files)."""

    def __init__(self, url: str) -> None:
        import google.cloud.storage as storage

        bucket, _, prefix = url.removeprefix("gs://").partition("/")
        self.bucket = storage.Client().bucket(bucket)
        self.prefix = prefix.strip("/")

    def put(self, name: str, data: bytes | Path, content_type: str) -> str:
        key = f"{self.prefix}/{name}" if self.prefix else name
        blob = self.bucket.blob(key)
        if isinstance(data, Path):
            blob.upload_from_filename(str(data), content_type=content_type)
        else:
            blob.upload_from_string(data, content_type=content_type)
        return f"gs://{self.bucket.name}/{key}"


def sink_for(destination: str) -> Sink:
    return GcsSink(destination) if destination.startswith("gs://") else LocalSink(Path(destination))


def process(
    report: Report,
    client: Any,
    work: Path,
    out: Sink,
    pdf_out: Sink | None = None,
) -> Result:
    """Download, extract, write `metrics/<doc_id>.jsonl` (and the PDF to the private sink)."""
    from belegt.documents.pdf import read_pages

    work.mkdir(parents=True, exist_ok=True)
    pdf = work / f"{report.doc_id}.pdf"
    size, sha256 = download(client, report.url, pdf)
    pages = list(read_pages(pdf, report.doc_id))
    found = list(metrics.extract(pages, report.decimal_comma))
    out.put(f"metrics/{report.doc_id}.jsonl", metrics_jsonl(found), "application/x-ndjson")
    if pdf_out is not None:
        pdf_out.put(f"pdf/{report.doc_id}.pdf", pdf, "application/pdf")
    pdf.unlink()
    return Result(
        doc_id=report.doc_id,
        bytes=size,
        sha256=sha256,
        pages=len(pages),
        candidates=len(found),
        selected={m.metric: m.value_t for m in found if m.selected and m.value_t is not None},
    )


def read_metrics(paths: Iterable[Path]) -> list[metrics.ReportedMetric]:
    """Rows of the `metrics/*.jsonl` files, for the raw table `reported_metrics`."""
    return [
        metrics.ReportedMetric(**json.loads(line))
        for path in paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
