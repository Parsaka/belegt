import json

from typer.testing import CliRunner

from belegt import cli
from belegt.api.app import load_chunks
from belegt.documents.model import Page


def test_index_is_idempotent_per_document(tmp_path, monkeypatch):
    from belegt.documents import pdf

    monkeypatch.setattr(
        pdf, "read_pages", lambda path, doc_id: iter([Page(doc_id, 1, "Scope 1: 5 t.")])
    )
    out = tmp_path / "chunks.jsonl"
    runner = CliRunner()
    for _ in range(2):
        result = runner.invoke(
            cli.app, ["index", "x.pdf", "--doc-id", "acme-2024", "--out", str(out)]
        )
        assert result.exit_code == 0, result.output
    runner.invoke(cli.app, ["index", "y.pdf", "--doc-id", "other-2024", "--out", str(out)])
    lines = [json.loads(line) for line in out.read_text().splitlines()]
    assert [line["doc_id"] for line in lines] == ["acme-2024", "other-2024"]
    assert load_chunks(out)[0].tenant_id == "shared"
