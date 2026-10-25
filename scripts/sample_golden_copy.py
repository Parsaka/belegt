"""Write a trimmed real sample of the golden-copy entities file for tests/fixtures (CC0).

    python scripts/sample_golden_copy.py data/raw/gleif_entities.csv out.csv

Keeps the rows of the LEIs already in the API fixture, so both fixture formats describe the
same entities and the loader can be checked for equal output.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

FIXTURE = Path(__file__).parents[1] / "tests" / "fixtures" / "gleif_entities_groups.json"


def main(source: str, out: str, limit: int = 25) -> None:
    records = json.loads(FIXTURE.read_text())
    german = [r for r in records if r["attributes"]["entity"]["legalAddress"]["country"] == "DE"]
    wanted = {r["attributes"]["lei"] for r in german[:limit]}
    with open(source, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = [r for r in reader if r["LEI"] in wanted]
    with open(out, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=reader.fieldnames or [])
        writer.writeheader()
        writer.writerows(sorted(rows, key=lambda r: r["LEI"]))
    print(f"{len(rows)} of {len(wanted)} entities -> {out}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
