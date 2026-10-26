"""Markdown summary of a report run, for the ops-results branch.

    python scripts/report_summary.py <out dir with metrics/> <results.jsonl> > summary.md

Reports are copyrighted: the summary holds the extracted figures with their page and the table
line they came from (at most 200 characters, a short factual quote), never page text.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from belegt.documents.reports import read_metrics


def main(out: Path, results: Path) -> None:
    print("# Report run\n")
    print("| report | pages | candidates | selected (t) | error |")
    print("|---|---|---|---|---|")
    for line in results.read_text().splitlines():
        if not line.startswith("{"):
            continue
        r = json.loads(line)
        selected = ", ".join(f"{k} {v:,.0f}" for k, v in sorted(r.get("selected", {}).items()))
        error = r.get("error", "").replace("|", "/")
        print(
            f"| {r['doc_id']} | {r.get('pages', '')} | {r.get('candidates', '')} | {selected} | {error} |"
        )
    print("\n## Candidates\n")
    print("| report | metric | t | page | rows on page | selected | table line |")
    print("|---|---|---|---|---|---|---|")
    for m in read_metrics(sorted((out / "metrics").glob("*.jsonl"))):
        value = f"{m.value_t:,.0f}" if m.value_t is not None else ""
        quote = m.quote[:200].replace("|", "/")
        mark = "yes" if m.selected else ""
        print(
            f"| {m.doc_id} | {m.metric} | {value} | {m.page} | {m.rows_on_page} | {mark} | {quote} |"
        )


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
