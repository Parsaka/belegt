"""Accuracy of the Scope 1-3 extractor against hand-labelled values.

`evals/reported_metrics.csv` holds one row per report and metric, labelled by reading the
report's greenhouse-gas table (E1-6 or the pre-CSRD equivalent): the value in tonnes for the
reporting year, the PDF pages that state it (the E1-6 table first; some reports repeat the
figure in a summary table), the figure as printed, and the table line. An empty value means
the report states no such figure, so the extractor must not select one either. A note starting
with "text layer:" marks a row whose PDF text is garbled: the figure then comes from the
printed page (as published elsewhere by the company), and the quote is the garbled line the
extractor reads.

Each report belongs to one split:

- `dev`: reports whose failures were used to change the extractor's rules;
- `test`: reports added after the rules were frozen, measured as they came.

A selected figure is correct when it is within 0.5 % of the label (tables round to the shown
decimals) and comes from one of the labelled pages. The report counts per metric and per split:

- correct, wrong value, wrong page (right value from another page), missed, and spurious (a
  figure where the label says there is none);
- precision (correct / selected) and recall (correct / labelled figures).
"""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from belegt.documents.metrics import METRICS

TOLERANCE = 0.005
OUTCOMES = ("correct", "wrong_value", "wrong_page", "missed", "spurious", "absent")


@dataclass(frozen=True)
class Label:
    doc_id: str
    metric: str
    value_t: float | None  # None: the report states no such figure
    pages: tuple[int, ...]  # the E1-6 table page first
    figure: str  # as printed, e.g. "1.014" or "8.862"
    quote: str
    split: str
    note: str = ""

    @property
    def readable(self) -> bool:
        """False when the PDF text layer garbles the printed figure."""
        return not self.note.startswith("text layer:")

    @property
    def page(self) -> int | None:
        return self.pages[0] if self.pages else None


@dataclass(frozen=True)
class Selected:
    doc_id: str
    metric: str
    value_t: float
    page: int
    quote: str


@dataclass(frozen=True)
class Outcome:
    label: Label
    selected: Selected | None

    @property
    def outcome(self) -> str:
        return judge(self.label, self.selected)


def read_labels(path: Path) -> list[Label]:
    labels = []
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            if row["metric"] not in METRICS or row["split"] not in {"dev", "test"}:
                raise ValueError(f"{row['doc_id']}: unknown metric or split in {row}")
            value = float(row["value_t"]) if row["value_t"] else None
            pages = tuple(int(p) for p in row["pages"].split(";") if p)
            if value is not None and not (pages and row["figure"] and row["quote"]):
                raise ValueError(f"{row['doc_id']} {row['metric']}: a value needs its page")
            note = (row.get("note") or "").strip()
            garbled = note.startswith("text layer:")
            if value is not None and not garbled and row["figure"] not in row["quote"]:
                raise ValueError(f"{row['doc_id']} {row['metric']}: figure not in its line")
            labels.append(
                Label(
                    row["doc_id"],
                    row["metric"],
                    value,
                    pages,
                    row["figure"],
                    row["quote"],
                    row["split"],
                    note,
                )
            )
    keys = [(label.doc_id, label.metric) for label in labels]
    if len(set(keys)) != len(keys):
        raise ValueError("one label per report and metric")
    return labels


def read_selected(lines: Iterable[str]) -> dict[tuple[str, str], Selected]:
    """The selected figures from `metrics/<doc_id>.jsonl` lines (see `belegt reports`)."""
    out = {}
    for line in lines:
        if not line.strip():
            continue
        m = json.loads(line)
        if m.get("selected") and m.get("value_t") is not None:
            out[(m["doc_id"], m["metric"])] = Selected(
                m["doc_id"], m["metric"], float(m["value_t"]), int(m["page"]), m["quote"]
            )
    return out


def judge(label: Label, selected: Selected | None) -> str:
    if label.value_t is None:
        return "absent" if selected is None else "spurious"
    if selected is None:
        return "missed"
    if abs(selected.value_t - label.value_t) > TOLERANCE * abs(label.value_t):
        return "wrong_value"
    return "correct" if selected.page in label.pages else "wrong_page"


def evaluate(
    labels: Iterable[Label], selected: Mapping[tuple[str, str], Selected], docs: set[str]
) -> list[Outcome]:
    """Outcomes for the labelled reports that were processed in this run (`docs`)."""
    return [
        Outcome(label, selected.get((label.doc_id, label.metric)))
        for label in labels
        if label.doc_id in docs
    ]


def score(outcomes: Iterable[Outcome]) -> dict[str, int | float]:
    counts = dict.fromkeys(OUTCOMES, 0)
    for o in outcomes:
        counts[o.outcome] += 1
    selected = counts["correct"] + counts["wrong_value"] + counts["wrong_page"] + counts["spurious"]
    labelled = counts["correct"] + counts["wrong_value"] + counts["wrong_page"] + counts["missed"]
    return {
        **counts,
        "precision": counts["correct"] / selected if selected else 0.0,
        "recall": counts["correct"] / labelled if labelled else 0.0,
    }


def _pct(x: float | int) -> str:
    return f"{100 * x:.1f} %"


def report(outcomes: list[Outcome], title: str = "Extraction accuracy") -> str:
    lines = [f"# {title}", ""]
    docs = {o.label.doc_id for o in outcomes}
    lines += [
        f"{len(docs)} labelled reports, {len(outcomes)} labels. A figure is correct within "
        f"{TOLERANCE:.1%} of the label and from the labelled page.",
        "",
        "| split | metric | correct | wrong value | wrong page | missed | spurious "
        "| precision | recall |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for split in ("dev", "test", "all"):
        in_split = [o for o in outcomes if split == "all" or o.label.split == split]
        if not in_split:
            continue
        for metric in (*METRICS, "all"):
            group = [o for o in in_split if metric == "all" or o.label.metric == metric]
            if not group:
                continue
            s = score(group)
            name = f"**{metric}**" if metric == "all" else metric
            lines.append(
                f"| {split} | {name} | {s['correct']} | {s['wrong_value']} | {s['wrong_page']} "
                f"| {s['missed']} | {s['spurious']} | {_pct(s['precision'])} "
                f"| {_pct(s['recall'])} |"
            )
    errors = [o for o in outcomes if o.outcome not in {"correct", "absent"}]
    if errors:
        lines += [
            "",
            "## Errors",
            "",
            "| report | metric | outcome | label (t, page) | selected (t, page) | selected line |",
            "|---|---|---|---|---|---|",
        ]
        for o in sorted(errors, key=lambda o: (o.label.doc_id, o.label.metric)):
            want = (
                f"{o.label.value_t:,.0f}, p.{o.label.page}" if o.label.value_t is not None else "-"
            )
            got = f"{o.selected.value_t:,.0f}, p.{o.selected.page}" if o.selected else "-"
            quote = o.selected.quote[:120].replace("|", "/") if o.selected else ""
            lines.append(
                f"| {o.label.doc_id} | {o.label.metric} | {o.outcome} | {want} | {got} | {quote} |"
            )
    return "\n".join(lines) + "\n"
