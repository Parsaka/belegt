from __future__ import annotations

import json
from pathlib import Path

import pytest

from belegt.documents import reports
from belegt.documents.evaluation import (
    Label,
    Outcome,
    Selected,
    evaluate,
    judge,
    read_labels,
    read_selected,
    report,
    score,
)

ROOT = Path(__file__).resolve().parents[1]
LABELS = ROOT / "evals" / "reported_metrics.csv"


def label(value: float | None, page: int | None = 10, split: str = "test") -> Label:
    pages = (page, 12) if page else ()
    return Label("acme-2024", "scope1", value, pages, "1.0", "Gross Scope 1 1.0", split)


def picked(value: float, page: int = 10) -> Selected:
    return Selected("acme-2024", "scope1", value, page, "Gross Scope 1 1.0")


@pytest.mark.parametrize(
    ("lab", "sel", "expected"),
    [
        (label(1_014_000), picked(1_014_000), "correct"),
        (label(1_014_000), picked(1_010_000), "correct"),  # within 0.5 %: rounding
        (label(1_014_000), picked(930_000), "wrong_value"),  # the prior year's column
        (label(1_014_000), picked(1_014_000, page=99), "wrong_page"),
        (label(1_014_000), picked(1_014_000, page=12), "correct"),  # the summary table
        (label(1_014_000), None, "missed"),
        (label(None, page=None), picked(5), "spurious"),
        (label(None, page=None), None, "absent"),
    ],
)
def test_judge(lab, sel, expected):
    assert judge(lab, sel) == expected


def test_score_counts_precision_over_selected_and_recall_over_labelled():
    outcomes = [
        Outcome(label(1.0), picked(1.0)),  # correct
        Outcome(label(1.0), picked(2.0)),  # wrong value
        Outcome(label(1.0), None),  # missed
        Outcome(label(None, None), picked(3.0)),  # spurious
    ]
    s = score(outcomes)
    assert (s["correct"], s["wrong_value"], s["missed"], s["spurious"]) == (1, 1, 1, 1)
    assert s["precision"] == pytest.approx(1 / 3)
    assert s["recall"] == pytest.approx(1 / 3)


def test_read_selected_keeps_only_the_selected_figure():
    lines = [
        json.dumps({"doc_id": "a", "metric": "scope1", "value_t": 1.0, "page": 3, "quote": "x"}),
        json.dumps(
            {
                "doc_id": "a",
                "metric": "scope1",
                "value_t": 2.0,
                "page": 4,
                "quote": "y",
                "selected": True,
            }
        ),
    ]
    assert read_selected(lines)[("a", "scope1")].value_t == 2.0


def test_evaluate_ignores_reports_this_run_did_not_process():
    labels = [label(1.0), Label("other-2024", "scope1", 1.0, (1,), "1", "1", "dev")]
    outcomes = evaluate(labels, {}, {"acme-2024"})
    assert [o.label.doc_id for o in outcomes] == ["acme-2024"]


def test_report_lists_errors_with_the_selected_line():
    text = report([Outcome(label(1_014_000), picked(930_000))])
    assert "| test | **all** | 0 | 1 |" in text
    assert "wrong_value" in text and "1,014,000, p.10" in text


def test_labels_cover_seed_reports_once_each(tmp_path):
    labels = read_labels(LABELS)
    seed = {r.doc_id: r for r in reports.read_seed(ROOT / "dbt" / "seeds" / "reports.csv")}
    assert {lab.doc_id for lab in labels} <= set(seed)
    assert {lab.split for lab in labels} == {"dev", "test"}
    for lab in labels:
        assert len(lab.quote) <= 200  # a table line, never more of the copyrighted report
        if lab.value_t is not None:
            assert lab.value_t > 0 and lab.page and lab.page > 0
            assert lab.figure in lab.quote or not lab.readable
    # every labelled report has all four metrics, so a missing figure is a decision, not a gap
    by_doc: dict[str, set[str]] = {}
    for lab in labels:
        by_doc.setdefault(lab.doc_id, set()).add(lab.metric)
    assert all(len(metrics) == 4 for metrics in by_doc.values())


def test_read_labels_rejects_a_value_without_page(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text("doc_id,metric,value_t,pages,figure,quote,split\nacme,scope1,5,,5,x 5,dev\n")
    with pytest.raises(ValueError, match="needs its page"):
        read_labels(path)


def test_a_garbled_line_keeps_the_printed_figure_with_a_note(tmp_path):
    path = tmp_path / "labels.csv"
    path.write_text(
        "doc_id,metric,value_t,pages,figure,quote,split,note\n"
        'acme,scope1,10135000,160,10.135,Scope 1 10.724 0.35,dev,"text layer: 0.35"\n'
        "acme,scope3,5,160,5,Scope 3 7,dev,\n"
    )
    with pytest.raises(ValueError, match="figure not in its line"):
        read_labels(path)
    path.write_text("\n".join(path.read_text().splitlines()[:2]) + "\n")
    (lab,) = read_labels(path)
    assert not lab.readable and lab.value_t == 10_135_000
