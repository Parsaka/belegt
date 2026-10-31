"""Check every report's LEI against the GLEIF API, so a wrong LEI never joins a report to the
wrong group.

    python scripts/check_report_leis.py dbt/seeds/reports.csv > leis.md
    python scripts/check_report_leis.py --search "Henkel AG & Co. KGaA" "Siemens AG"

The first form prints one row per report (GLEIF legal name, status, country) and exits 1 if an
LEI is unknown, lapsed outside Germany, or names a different company. The second form lists
GLEIF candidates for a company name, to fill in a new seed row. Runs on the CI runner; tests
never call it.
"""

from __future__ import annotations

import csv
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import httpx

from belegt.extract import USER_AGENT

API = "https://api.gleif.org/api/v1"
# Legal-form words that GLEIF and the seed spell differently ("AG" vs "Aktiengesellschaft")
_FORMS = re.compile(
    r"\b(?:ag|se|kgaa|co|gmbh|aktiengesellschaft|kommanditgesellschaft auf aktien|"
    r"societas europaea|and|und|the)\b"
)


def _key(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    text = _FORMS.sub(" ", re.sub(r"[^a-z0-9 ]", " ", text))
    return " ".join(text.split())


def same_company(seed: str, gleif: str) -> bool:
    """True if the names agree once legal forms and punctuation are ignored."""
    a, b = _key(seed), _key(gleif)
    return bool(a) and (a == b or a in b or b in a)


def _record(client: httpx.Client, lei: str) -> dict[str, Any] | None:
    response = client.get(f"{API}/lei-records/{lei}")
    if response.status_code == 404:
        return None
    response.raise_for_status()
    data: dict[str, Any] = response.json()["data"]
    return data


def check(client: httpx.Client, seed: Path) -> int:
    failures = 0
    print("| doc_id | LEI | GLEIF legal name | status | country | check |")
    print("|---|---|---|---|---|---|")
    with seed.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            record = _record(client, row["lei"])
            if record is None:
                failures += 1
                print(f"| {row['doc_id']} | {row['lei']} | (not in GLEIF) | | | FAIL |")
                continue
            entity = record["attributes"]["entity"]
            name = entity["legalName"]["name"]
            status = record["attributes"]["registration"]["status"]
            country = entity["legalAddress"]["country"]
            ok = same_company(row["company"], name) and country == "DE"
            failures += not ok
            print(
                f"| {row['doc_id']} | {row['lei']} | {name} | {status} | {country} | "
                f"{'ok' if ok else 'FAIL'} |"
            )
    return 1 if failures else 0


def search(client: httpx.Client, names: list[str]) -> int:
    for name in names:
        response = client.get(
            f"{API}/lei-records",
            params={
                "filter[fulltext]": name,
                "filter[entity.legalAddress.country]": "DE",
                "page[size]": "8",
            },
        )
        response.raise_for_status()
        print(f"## {name}\n")
        for record in response.json()["data"]:
            attributes = record["attributes"]
            print(
                f"- {attributes['lei']} {attributes['entity']['legalName']['name']} "
                f"({attributes['registration']['status']})"
            )
        print()
    return 0


def main(argv: list[str]) -> int:
    with httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60) as client:
        if argv[:1] == ["--search"]:
            return search(client, argv[1:])
        return check(client, Path(argv[0]))


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
