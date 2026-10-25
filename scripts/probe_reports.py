"""Where the Scope 1-3 figures sit in each downloaded report, to tune the extractor.

    python scripts/probe_reports.py <dir with pdf/*.pdf> > probe.md

Runs only on the CI runner, next to PDFs that never leave it. The output holds page numbers
and at most 25 short lines (160 characters) per report that mention a scope or the E1-6 table.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from belegt.documents.metrics import page_unit
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
        table = [h for h in hits if re.search(r"\d", h[1])]
        for number, line in table[:25]:
            print(f"    p.{number}: {line[:160]}")
        print()


if __name__ == "__main__":
    main(Path(sys.argv[1]))
