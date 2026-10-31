"""Where the Scope 1-3 figures sit in each downloaded report, to tune the extractor.

    python scripts/probe_reports.py <dir with pdf/*.pdf> > probe.md
    python scripts/probe_reports.py <dir> "bmw-2024:195-196,200;k-s-2024:100" > pages.md

Runs only on the CI runner, next to PDFs that never leave it. The output holds page numbers
and, for at most six likely E1-6 table pages per report, up to 80 lines with figures (160
characters each): enough to label the table by hand (`evals/reported_metrics.csv`). With a
page list, only those pages of those reports, for tables the page ranking does not find.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from belegt.documents.metrics import _rows, metric_of, page_unit
from belegt.documents.pdf import read_pages
from belegt.documents.reports import read_seed

_HINT = re.compile(r"\bScope[\s-]*[123]\b|E1-6", re.I)
_FIGURE = re.compile(r"(?<![\d.,])\d{1,3}(?:[.,]\d{3})+(?:[.,]\d+)?|\b\d+[.,]\d+\b|\b\d{3,}\b")


def parse_pages(spec: str) -> dict[str, set[int]]:
    """`doc:1-3,7;doc2:9;doc3:` -> {doc: {1, 2, 3, 7}, doc2: {9}, doc3: set()}

    No pages: the lines that mention a scope, wherever they are."""
    out: dict[str, set[int]] = {}
    for part in filter(None, (p.strip() for p in spec.split(";"))):
        doc, _, ranges = part.partition(":")
        out.setdefault(doc.strip(), set())
        for r in filter(None, (r.strip() for r in ranges.split(","))):
            lo, _, hi = r.partition("-")
            out[doc.strip()].update(range(int(lo), int(hi or lo) + 1))
    return out


def numeric_lines(text: str, limit: int = 80) -> list[str]:
    lines = (re.sub(r"\s+", " ", line).strip() for line in text.splitlines())
    return [line[:160] for line in lines if re.search(r"\d", line)][:limit]


def main(root: Path) -> None:
    for pdf in sorted((root / "pdf").glob("*.pdf")):
        pages = list(read_pages(pdf, pdf.stem))
        hits = [
            (p.number, re.sub(r"\s+", " ", line).strip())
            for p in pages
            for line in p.text.splitlines()
            if _HINT.search(line)
        ]
        e16 = sorted({n for n, line in hits if "E1-6" in line})
        units = [p.number for p in pages if page_unit(p.text)]
        print(f"## {pdf.stem}\n")
        print(
            f"- pages: {len(pages)}; pages without text: {sum(not p.text.strip() for p in pages)}"
        )
        print(f"- pages that mention E1-6: {e16[:20]}")
        print(f"- pages with a CO2 unit: {units[:30]}")
        print(f"- lines that mention a scope: {len(hits)}\n")
        # Likely tables: pages with at least two scope rows whose figures sit on the row or on
        # one of the two lines below it (wrapped rows: label / unit / figures)
        rows: dict[int, int] = {}
        for page in pages:
            lines = [re.sub(r"\s+", " ", line).strip() for line in page.text.splitlines()]
            for i, line in enumerate(lines):
                near = " ".join([line[12:], *lines[i + 1 : i + 3]])
                if metric_of(line) and _FIGURE.search(near):
                    rows[page.number] = rows.get(page.number, 0) + 1
        # the pages with the most scope rows first: the E1-6 table is one of them
        dense = sorted((n for n, c in rows.items() if c >= 2), key=lambda n: -rows[n])[:4]
        # tables run over onto the next page (Scope 3 often sits there); E1-6 mentions are
        # mostly index tables, so they only fill in when no page has a table
        likely = sorted(set(dense) | {n + 1 for n in dense[:2]}) if dense else e16[:2]
        for page in (p for p in pages if p.number in likely):
            print(f"    p.{page.number} (lines with figures):")
            for line in numeric_lines(page.text):
                print(f"      {line}")
        print()


def show(root: Path, wanted: dict[str, set[int]]) -> None:
    seed = {r.doc_id: r for r in read_seed(Path("dbt/seeds/reports.csv"))}
    for doc, numbers in sorted(wanted.items()):
        comma = seed[doc].decimal_comma if doc in seed else False
        pdf = root / "pdf" / f"{doc}.pdf"
        if not pdf.exists():
            print(f"## {doc}\n\n- not downloaded\n")
            continue
        print(f"## {doc}\n")
        few = set(sorted(numbers)[:8])  # a few table pages, never the report
        pages = list(read_pages(pdf, doc))
        if not numbers:
            hits = [
                f"p.{page.number}: {line[:160]}"
                for page in pages
                for line in (re.sub(r"\s+", " ", raw).strip() for raw in page.text.splitlines())
                if _HINT.search(line)
            ]
            print("\n".join(f"      {hit}" for hit in hits[:40]))
        for page in pages:
            if page.number in few:
                print(f"    p.{page.number} (all lines):")
                lines = (re.sub(r"\s+", " ", raw).strip() for raw in page.text.splitlines())
                for line in [line for line in lines if line][:100]:
                    print(f"      {line[:160]}")
                # how the extractor reads the page: each scope row with the header years above it
                print(f"    p.{page.number} (scope rows as the extractor reads them):")
                for row, header, _ in _rows(page.text, comma):
                    if metric_of(row):
                        print(f"      {header} | {row[:120]}")
        print()


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[2].strip():
        show(Path(sys.argv[1]), parse_pages(sys.argv[2]))
    else:
        main(Path(sys.argv[1]))
