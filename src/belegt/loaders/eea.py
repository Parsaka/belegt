"""EEA Industrial Reporting (CC BY 4.0): ETS ids, installations and facilities with parent company.

Exported from the Access database with mdb-export. The chain is
ETSIdentifier -> Installation_INSPIRE_ID -> Parent_Facility_INSPIRE_ID -> parentCompanyName.
"""

from __future__ import annotations

import csv
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EtsLink:
    ets_identifier: str
    installation_inspire_id: str
    reporting_year: int


@dataclass(frozen=True)
class Installation:
    installation_inspire_id: str
    facility_inspire_id: str
    name: str
    activity_code: str | None


@dataclass(frozen=True)
class Facility:
    facility_inspire_id: str
    name: str
    parent_company_name: str | None
    city: str | None
    country: str | None
    lat: float | None
    lon: float | None


def _rows(path: Path) -> Iterator[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh)


def _opt(text: str | None) -> str | None:
    return text.strip() or None if text else None


def _float(text: str | None) -> float | None:
    return float(text) if text and text.strip() else None


def read_ets_links(path: Path) -> Iterator[EtsLink]:
    for r in _rows(path):
        yield EtsLink(
            r["ETSIdentifier"].strip(), r["Installation_INSPIRE_ID"], int(r["reportingYear"])
        )


def read_installations(path: Path) -> Iterator[Installation]:
    for r in _rows(path):
        yield Installation(
            r["Installation_INSPIRE_ID"],
            r["Parent_Facility_INSPIRE_ID"],
            r["nameOfFeature"].strip(),
            _opt(r.get("mainActivityCode")),
        )


def read_facilities(path: Path) -> Iterator[Facility]:
    for r in _rows(path):
        yield Facility(
            r["Facility_INSPIRE_ID"],
            r["nameOfFeature"].strip(),
            _opt(r.get("parentCompanyName")),
            _opt(r.get("city")),
            _opt(r.get("countryCode")),
            _float(r.get("pointGeometryLat")),
            _float(r.get("pointGeometryLon")),
        )
