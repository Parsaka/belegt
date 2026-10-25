"""Where the Scope 1-3 figures sit in each downloaded report, to tune the extractor.

    python scripts/probe_reports.py <dir with pdf/*.pdf> > probe.md

Runs only on the CI runner, next to PDFs that never leave it. The output holds page numbers
and, for at most six likely E1-6 table pages per report, up to 40 lines with figures (120
characters each).
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from belegt.documents.metrics import metric_of, page_unit
from belegt.documents.pdf import read_pages

_HINT = re.compile(r"\bScope[\s-]*[123]\b|E1-6", re.I)


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
        # Likely tables: pages with at least two scope rows that carry figures, plus E1-6 pages
        rows: dict[int, int] = {}
        for n, line in hits:
            if metric_of(line) and re.search(r"\d[.,]?\d", line[12:]):
                rows[n] = rows.get(n, 0) + 1
        likely = sorted({n for n, c in rows.items() if c >= 2} | set(e16[:3]))[:6]
        for page in (p for p in pages if p.number in likely):
            print(f"    p.{page.number} (lines with figures):")
            numeric = [
                re.sub(r"\s+", " ", line).strip()
                for line in page.text.splitlines()
                if re.search(r"\d", line)
            ]
            for line in numeric[:40]:
                print(f"      {line[:120]}")
        print()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
