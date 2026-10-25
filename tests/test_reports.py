"""Report tasks: seed, task index, download guards, and one synthetic report end to end."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

import pytest

from belegt.documents import reports
from belegt.documents.synthetic import statement

ROOT = Path(__file__).parents[1]
SEED = ROOT / "dbt" / "seeds" / "reports.csv"


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200) -> None:
        self.body = body
        self.status = status
        self.headers = {"content-type": "text/html" if not body.startswith(b"%PDF") else "pdf"}
        self.url = "https://final.test/x"

    def raise_for_status(self) -> None:
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    def iter_bytes(self, size: int):
        for i in range(0, len(self.body), size):
            yield self.body[i : i + size]


class FakeClient:
    def __init__(self, bodies: dict[str, bytes]) -> None:
        self.bodies = bodies

    @contextmanager
    def stream(self, method: str, url: str):
        assert method == "GET"
        yield FakeResponse(self.bodies[url])


def test_seed_rows_are_complete_and_unique():
    rows = reports.read_seed(SEED)
    assert len({r.doc_id for r in rows}) == len(rows) >= 7
    for r in rows:
        assert len(r.lei) == 20 and r.url.startswith("https://")
        assert r.fiscal_year_end in {"12-31", "09-30"}
        assert r.language in {"de", "en"}  # decides the decimal separator


def test_task_index_comes_from_kubernetes_or_cloud_run():
    assert reports.task_index({}) is None
    assert reports.task_index({"JOB_COMPLETION_INDEX": "3"}) == 3
    assert reports.task_index({"CLOUD_RUN_TASK_INDEX": "0"}) == 0


def test_download_refuses_html(tmp_path):
    client = FakeClient({"u": b"<!DOCTYPE html><p>Cookie consent</p>"})
    with pytest.raises(reports.ReportError, match=r"did not return a PDF \(text/html, final"):
        reports.download(client, "u", tmp_path / "x.pdf")


def test_download_refuses_oversized_files(tmp_path, monkeypatch):
    monkeypatch.setattr(reports, "MAX_BYTES", 10)
    client = FakeClient({"u": b"%PDF-1.4" + b"x" * 20})
    with pytest.raises(reports.ReportError, match="larger than"):
        reports.download(client, "u", tmp_path / "x.pdf")


def test_a_synthetic_report_yields_cited_figures(tmp_path):
    pytest.importorskip("pypdf")
    report = reports.Report(
        "acme-2024", "Acme AG", "5299000000000000ACME", 2024, "12-31", "de", "u", "test"
    )
    client = FakeClient({"u": statement("Acme AG", "10,4", "1,1", "52,3")})
    out = reports.LocalSink(tmp_path / "out")
    private = reports.LocalSink(tmp_path / "private")

    result = reports.process(report, client, tmp_path / "work", out, private)

    assert result.pages == 3
    assert result.selected == {
        "scope1": 10_400_000.0,
        "scope2_market": 1_100_000.0,
        "scope3": 52_300_000.0,
    }
    rows = reports.read_metrics([tmp_path / "out" / "metrics" / "acme-2024.jsonl"])
    scope1 = next(r for r in rows if r.metric == "scope1" and r.selected)
    assert scope1.page == 3 and scope1.quote.startswith("Scope 1 THG-Emissionen 10,4")
    # the prose on page 2 has only one figure and is no candidate at all
    assert all(r.page == 3 for r in rows)
    # the PDF went to the private sink only; nothing is left in the work directory
    assert (tmp_path / "private" / "pdf" / "acme-2024.pdf").exists()
    assert not list((tmp_path / "work").iterdir())
    assert not list((tmp_path / "out").rglob("*.pdf"))


def test_cli_reports_one_task_and_survives_a_bad_host(tmp_path, monkeypatch):
    pytest.importorskip("pypdf")
    httpx = pytest.importorskip("httpx")
    from typer.testing import CliRunner

    from belegt import cli

    seed = tmp_path / "reports.csv"
    seed.write_text(
        "doc_id,company,lei,report_year,fiscal_year_end,language,url,host_note\n"
        "good-2024,Good AG,5299000000000000GOOD,2024,12-31,de,https://a.test/good.pdf,t\n"
        "bad-2024,Bad AG,5299000000000000BADX,2024,12-31,de,https://a.test/bad.pdf,t\n"
    )
    pdf = statement("Good AG", "1,0", "0,1", "3,0")

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/good.pdf":
            return httpx.Response(200, content=pdf)
        return httpx.Response(200, content=b"<html>moved</html>")

    real_client = httpx.Client
    monkeypatch.setattr(
        httpx, "Client", lambda **kw: real_client(transport=httpx.MockTransport(handler), **kw)
    )
    runner = CliRunner()
    args = ["reports", "--seed", str(seed), "--out", str(tmp_path / "raw" / "reports")]
    args += ["--work", str(tmp_path / "work")]

    every = runner.invoke(cli.app, args)
    assert every.exit_code == 0, every.output
    lines = [json.loads(line) for line in every.output.splitlines()]
    assert lines[0]["selected"]["scope1"] == 1_000_000.0
    assert "did not return a PDF" in lines[1]["error"]

    monkeypatch.setenv("JOB_COMPLETION_INDEX", "1")
    one = runner.invoke(cli.app, args)
    assert one.exit_code == 1  # the scheduler retries this task
    assert json.loads(one.output)["doc_id"] == "bad-2024"


def test_metrics_land_in_the_raw_table(tmp_path):
    duckdb = pytest.importorskip("duckdb")
    from belegt.documents.metrics import ReportedMetric
    from belegt.warehouse import write_table

    row = ReportedMetric("acme-2024", "scope1", 10.0, 3, "Mio. t", "Scope 1 10 9", 3, True)
    path = tmp_path / "m.jsonl"
    path.write_bytes(reports.metrics_jsonl([row]))
    con = duckdb.connect()
    con.execute("CREATE SCHEMA raw")
    assert write_table(con, "reported_metrics", ReportedMetric, reports.read_metrics([path])) == 1
    assert con.execute("select selected, page from raw.reported_metrics").fetchall() == [(True, 3)]
