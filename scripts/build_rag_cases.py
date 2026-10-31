"""Build the document assistant's cases on real reports from the hand labels.

    python scripts/build_rag_cases.py > evals/rag_report_cases.jsonl

For every report in `evals/rag_corpus.csv` with a labelled Scope 1 figure, two cases:

- its owner asks for the figure: the answer must cite that report on a labelled page and
  contain the figure as printed;
- the other tenant asks the same question: it must abstain, and citing the report would be a
  leak.

Labels whose PDF text layer garbles the figure are left out: the assistant quotes the text
layer, so it cannot contain the printed figure. The labels decide what is right, so the assistant is measured against the same hand-checked
values as the extractor (see `belegt.documents.evaluation`). A test keeps the file in sync.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TENANTS = ("tenant_a", "tenant_b")
QUESTION = {
    "en": "What were {name}'s gross Scope 1 GHG emissions in {year}?",
    "de": "Wie hoch waren die Scope-1-Emissionen von {name} im Jahr {year}?",
}


def build(root: Path = ROOT) -> list[dict[str, object]]:
    def rows(path: str) -> list[dict[str, str]]:
        with (root / path).open(newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    seed = {r["doc_id"]: r for r in rows("dbt/seeds/reports.csv")}
    corpus = {r["doc_id"]: r for r in rows("evals/rag_corpus.csv")}
    cases: list[dict[str, object]] = []
    for label in rows("evals/reported_metrics.csv"):
        doc = label["doc_id"]
        if label["metric"] != "scope1" or not label["value_t"] or doc not in corpus:
            continue
        if (label.get("note") or "").startswith("text layer:"):
            continue  # the assistant reads the text layer too: a garbled figure is not there
        report, owner = seed[doc], corpus[doc]["tenant"]
        other = next(t for t in TENANTS if t != owner)
        question = QUESTION[report["language"]].format(
            name=corpus[doc]["name"], year=report["report_year"]
        )
        pages = [int(p) for p in label["pages"].split(";")]
        cases.append(
            {
                "id": f"{doc}-scope1",
                "tenant": owner,
                "question": question,
                "expect": "answer",
                "doc": doc,
                "contains": label["figure"],
                "pages": pages,
            }
        )
        cases.append(
            {
                "id": f"{doc}-scope1-other-tenant",
                "tenant": other,
                "question": question,
                "expect": "abstain",
            }
        )
    return cases


def render(cases: list[dict[str, object]]) -> str:
    return "".join(json.dumps(c, ensure_ascii=False) + "\n" for c in cases)


if __name__ == "__main__":
    sys.stdout.write(render(build()))
