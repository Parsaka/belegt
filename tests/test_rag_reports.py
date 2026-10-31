"""The document assistant on real reports: table rows as answers, company names as
identifiers, page-checked citations. Page texts are written like the real tables; the PDFs are
copyrighted and never committed."""

from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from typer.testing import CliRunner

from belegt.cli import app
from belegt.documents.chunking import chunk_pages
from belegt.documents.model import Page
from belegt.documents.synthetic import pdf_bytes
from belegt.rag.answer import Answerer
from belegt.rag.embedding import HashingEmbedder
from belegt.rag.evals import Case, judge
from belegt.rag.extractive import ExtractiveModel, entity_words, report_entities
from belegt.rag.names import ReportNames
from belegt.rag.retrieval import InMemoryRetriever

ROOT = Path(__file__).resolve().parents[1]
SEED = ROOT / "dbt" / "seeds" / "reports.csv"

COVESTRO = Page(
    "covestro-2024",
    160,
    "GHG emissions (million metric tons of CO2equivalents)\n"
    "Base year 2023 2024 Change\n"
    "Gross Scope 1 GHG emissions 1.25 0.93 1.014 9%\n"
    "Gross market-based Scope 2 GHG emissions 4.33 4.18 3.84 -8%",
)
LUFTHANSA = Page(
    "lufthansa-2024",
    163,
    "(2019) 2023 2024 Change in %\n"
    "Gross Scope 1 GHG emissions in 1,000 tonnes CO2e 33,349 26,822 29,159 9%",
)
SIEMENS_ENERGY = Page("siemens-energy-2024", 2, "Gross Scope 1 GHG emissions 175 160")
SIEMENS = Page("siemens-2024", 40, "Gross Scope 1 GHG emissions 433 504")


def chunks(page: Page, tenant: str, title: str):
    return list(chunk_pages([page], tenant, title=title))


def assistant(*corpus, entities=()):
    retriever = InMemoryRetriever(HashingEmbedder(), [c for part in corpus for c in part])
    return Answerer(retriever, ExtractiveModel(entities), min_score=0.0)


ENTITIES = entity_words(
    ["Covestro AG", "Deutsche Lufthansa Aktiengesellschaft", "Siemens Energy AG", "Siemens"]
)


def test_a_table_row_answers_with_the_title_naming_the_company():
    bot = assistant(
        chunks(COVESTRO, "tenant_a", "Covestro AG, report 2024"),
        chunks(LUFTHANSA, "tenant_a", "Deutsche Lufthansa Aktiengesellschaft, report 2024"),
        entities=ENTITIES,
    )
    answer = bot.ask("What were Covestro's gross Scope 1 GHG emissions in 2024?", "tenant_a")
    assert not answer.abstained
    assert "1.014" in answer.text and answer.citations[0].startswith("covestro-2024:160:")


def test_another_companys_row_never_answers_a_question_about_a_company():
    bot = assistant(
        chunks(LUFTHANSA, "tenant_b", "Deutsche Lufthansa Aktiengesellschaft, report 2024"),
        entities=ENTITIES,
    )
    # tenant_b cannot see Covestro; Lufthansa's Scope 1 row matches every other word
    answer = bot.ask("What were Covestro's gross Scope 1 GHG emissions in 2024?", "tenant_b")
    assert answer.abstained


def test_the_source_that_names_exactly_the_asked_company_wins():
    bot = assistant(
        chunks(SIEMENS_ENERGY, "tenant_b", "Siemens Energy AG, report 2024"),
        chunks(SIEMENS, "tenant_b", "Siemens Aktiengesellschaft, report 2024"),
        entities=ENTITIES,
    )
    answer = bot.ask("What were Siemens's gross Scope 1 GHG emissions in 2024?", "tenant_b")
    assert answer.citations[0].startswith("siemens-2024:")


def test_entity_words_drop_legal_forms():
    assert entity_words(["K+S Aktiengesellschaft", "Mercedes-Benz Group AG"]) == {
        "k",
        "s",
        "mercedes",
        "benz",
    }
    assert {"bmw", "basf"} <= report_entities(SEED)


def test_a_citation_must_point_to_a_labelled_page():
    case = Case("c", "tenant_a", "q", "answer", doc="covestro-2024", contains="1.014", pages=[160])
    owners = {"covestro-2024": "tenant_a"}
    assert judge(case, "1.014 [covestro-2024:160:ab]", False, ["covestro-2024:160:ab"], owners)
    wrong = judge(case, "1.014 [covestro-2024:12:ab]", False, ["covestro-2024:12:ab"], owners)
    assert not wrong.passed and "not p.160" in wrong.note


def test_index_reports_keeps_climate_pages_with_title_and_owner(tmp_path, monkeypatch):
    monkeypatch.chdir(ROOT)
    pdfs = tmp_path / "pdf"
    pdfs.mkdir()
    (pdfs / "covestro-2024.pdf").write_bytes(
        pdf_bytes([["Report of the Supervisory Board"], ["Gross Scope 1 GHG emissions 1.014"]])
    )
    out = tmp_path / "chunks.jsonl"
    result = CliRunner().invoke(app, ["index-reports", str(pdfs), "--out", str(out)])
    assert result.exit_code == 0, result.output
    rows = [json.loads(line) for line in out.read_text().splitlines()]
    assert [(r["doc_id"], r["page"], r["tenant_id"]) for r in rows] == [
        ("covestro-2024", 2, "tenant_a")
    ]
    assert rows[0]["title"] == "Covestro AG, report 2024"


def test_corpus_names_identify_their_report():
    with SEED.open(newline="", encoding="utf-8") as fh:
        seed = {r["doc_id"]: r for r in csv.DictReader(fh)}
    with (ROOT / "evals" / "rag_corpus.csv").open(newline="", encoding="utf-8") as fh:
        corpus = list(csv.DictReader(fh))
    assert {r["tenant"] for r in corpus} == {"tenant_a", "tenant_b"}
    for row in corpus:
        own = entity_words([seed[row["doc_id"]]["company"], row["doc_id"]])
        assert entity_words([row["name"]]) <= own, row


def test_report_cases_are_built_from_the_labels():
    spec = importlib.util.spec_from_file_location("cases", ROOT / "scripts/build_rag_cases.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    built = module.render(module.build(ROOT))
    assert (ROOT / "evals" / "rag_report_cases.jsonl").read_text() == built
    cases = [json.loads(line) for line in built.splitlines()]
    assert sum(c["expect"] == "answer" for c in cases) == sum(
        c["expect"] == "abstain" for c in cases
    )


def test_a_question_names_the_reports_of_its_company():
    names = ReportNames(
        [
            ("basf-2024", "BASF SE"),
            ("k-s-2024", "K+S Aktiengesellschaft"),
            ("siemens-2024", "Siemens Aktiengesellschaft"),
            ("siemens-energy-2024", "Siemens Energy AG"),
        ]
    )
    # "BASF's" names BASF, not K+S through its "s"
    assert names.named("What were BASF's gross Scope 1 GHG emissions?") == {"basf-2024"}
    assert names.named("Scope 1 of Siemens Energy?") == {"siemens-energy-2024"}
    assert names.named("Scope 1 of Siemens?") == {"siemens-2024", "siemens-energy-2024"}
    assert names.named("Was verlangt ESRS E1-6?") is None


def test_retrieval_searches_only_the_named_company_among_alike_tables():
    # twenty reports with the same table: only the name tells them apart
    others = [
        Page(f"peer{i}-2024", 10, "Gross Scope 1 GHG emissions in 2024 1.0 2.0 3.0")
        for i in range(20)
    ]
    corpus = [c for p in others for c in chunks(p, "tenant_a", "Peer AG, report 2024")]
    corpus += chunks(COVESTRO, "tenant_a", "Covestro AG, report 2024")
    names = ReportNames([("covestro-2024", "Covestro AG")] + [(p.doc_id, "Peer") for p in others])
    retriever = InMemoryRetriever(HashingEmbedder(), corpus)
    bot = Answerer(retriever, ExtractiveModel(names.words), min_score=0.0, k=2, names=names)
    answer = bot.ask("What were Covestro's gross Scope 1 GHG emissions in 2024?", "tenant_a")
    assert answer.citations[0].startswith("covestro-2024:160:") and "1.014" in answer.text


def test_the_row_with_its_figures_beats_the_heading_and_prose():
    page = Page(
        "merck-2024",
        178,
        "Scope-1-Treibhausgasemissionen\n"
        "Wir überwachen unsere Scope-1-Emissionen vierteljährlich anhand von Daten.\n"
        "Scope-1-THG-Bruttoemissionen 1.827.123 858.053 913.561 5,0\n"
        "Marktbezogene Scope-2-THG-Bruttoemissionen 324.698 227.070 162.349 5,0",
    )
    bot = assistant(chunks(page, "tenant_a", "Merck KGaA, report 2024"), entities={"merck"})
    answer = bot.ask("Wie hoch waren die Scope-1-Emissionen von Merck im Jahr 2024?", "tenant_a")
    assert answer.text.startswith("Scope-1-THG-Bruttoemissionen 1.827.123 858.053")


def test_the_digit_of_a_figure_is_not_a_scope():
    page = Page("lanxess-2024", 136, "Gross Scope 2 GHG emissions 2,203 1,887 1,300")
    bot = assistant(chunks(page, "tenant_a", "LANXESS AG, report 2024"), entities={"lanxess"})
    assert bot.ask("What were LANXESS's gross Scope 1 GHG emissions?", "tenant_a").abstained


def test_chunks_keep_table_rows_whole():
    rows = "\n".join(f"Row {i} Gross Scope 1 GHG emissions 1,{i:03d} 2,{i:03d}" for i in range(80))
    parts = list(chunk_pages([Page("x-2024", 3, rows)], "tenant_a", max_chars=300, overlap=60))
    assert len(parts) > 5
    lines = {line for part in parts for line in part.text.split("\n")}
    assert lines == set(rows.split("\n"))  # every line whole, none cut
    assert all(len(part.text) <= 300 for part in parts)
