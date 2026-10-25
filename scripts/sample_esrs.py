"""Write a few real ESRS pages for tests/fixtures (EU legal text, reuse with attribution).

    python scripts/sample_esrs.py data/raw/esrs_de.pdf out.jsonl

Keeps the pages about E1-6 (gross Scope 1, 2 and 3 emissions), the disclosure the
consistency check and the eval questions are about.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from belegt.documents.pdf import read_pages


def main(pdf: str, out: str, limit: int = 6) -> None:
    pages = [p for p in read_pages(Path(pdf), "esrs-2023-2772") if "E1-6" in p.text]
    with open(out, "w", encoding="utf-8") as fh:
        for page in pages[:limit]:
            fh.write(json.dumps(asdict(page), ensure_ascii=False) + "\n")
    print(f"{min(len(pages), limit)} of {len(pages)} pages mentioning E1-6 -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
