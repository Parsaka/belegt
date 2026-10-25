"""GLEIF Level 1 (who is who) and Level 2 relationship records (who owns whom), CC0."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class LegalEntity:
    lei: str
    legal_name: str
    country: str | None
    city: str | None
    registered_as: str | None  # e.g. "HRB 6000", the Handelsregister number
    registered_at: str | None  # GLEIF registration authority id, e.g. RA000291
    legal_form: str | None
    entity_status: str
    registration_status: str
    last_update: str


@dataclass(frozen=True)
class Relationship:
    child_lei: str
    parent_lei: str
    relationship_type: str  # IS_DIRECTLY_CONSOLIDATED_BY or IS_ULTIMATELY_CONSOLIDATED_BY
    status: str
    valid_from: date | None
    valid_to: date | None
    registration_status: str


def entity_from_api(record: dict[str, Any]) -> LegalEntity:
    a = record["attributes"]
    e = a["entity"]
    addr = e.get("legalAddress") or {}
    return LegalEntity(
        lei=a["lei"],
        legal_name=e["legalName"]["name"],
        country=addr.get("country"),
        city=addr.get("city"),
        registered_as=e.get("registeredAs"),
        registered_at=(e.get("registeredAt") or {}).get("id"),
        legal_form=(e.get("legalForm") or {}).get("id"),
        entity_status=e["status"],
        registration_status=a["registration"]["status"],
        last_update=a["registration"]["lastUpdateDate"],
    )


def _opt(text: str | None) -> str | None:
    return text.strip() or None if text else None


def entity_from_golden_copy(row: dict[str, str]) -> LegalEntity:
    """The same record from the golden-copy LEI-CDF CSV (as written by `belegt extract`)."""
    return LegalEntity(
        lei=row["LEI"],
        legal_name=row["Entity.LegalName"].strip(),
        country=_opt(row["Entity.LegalAddress.Country"]),
        city=_opt(row["Entity.LegalAddress.City"]),
        registered_as=_opt(row["Entity.RegistrationAuthority.RegistrationAuthorityEntityID"]),
        registered_at=_opt(row["Entity.RegistrationAuthority.RegistrationAuthorityID"]),
        legal_form=_opt(row["Entity.LegalForm.EntityLegalFormCode"]),
        entity_status=row["Entity.EntityStatus"],
        registration_status=row["Registration.RegistrationStatus"],
        last_update=row["Registration.LastUpdateDate"],
    )


def read_entities(path: Path) -> Iterator[LegalEntity]:
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            yield entity_from_golden_copy(row)


def _date(text: str) -> date | None:
    return date.fromisoformat(text[:10]) if text else None


CONSOLIDATION = {"IS_DIRECTLY_CONSOLIDATED_BY", "IS_ULTIMATELY_CONSOLIDATED_BY"}


def period(row: dict[str, str]) -> tuple[date | None, date | None]:
    """Up to five periods per record. The relationship period says when the parent held the child;
    the accounting period only says which statements were consolidated, so it is the fallback."""
    found: dict[str, tuple[date | None, date | None]] = {}
    for n in range(1, 6):
        kind = row.get(f"Relationship.Period.{n}.periodType", "")
        if kind and kind not in found:
            found[kind] = (
                _date(row.get(f"Relationship.Period.{n}.startDate", "")),
                _date(row.get(f"Relationship.Period.{n}.endDate", "")),
            )
    return found.get("RELATIONSHIP_PERIOD") or found.get("ACCOUNTING_PERIOD") or (None, None)


def relationships(rows: Iterable[dict[str, str]]) -> Iterator[Relationship]:
    """Accounting-consolidation edges from golden-copy RR rows. Fund relations are skipped."""
    for row in rows:
        kind = row["Relationship.RelationshipType"]
        if kind not in CONSOLIDATION:
            continue
        valid_from, valid_to = period(row)
        yield Relationship(
            child_lei=row["Relationship.StartNode.NodeID"],
            parent_lei=row["Relationship.EndNode.NodeID"],
            relationship_type=kind,
            status=row["Relationship.RelationshipStatus"],
            valid_from=valid_from,
            valid_to=valid_to,
            registration_status=row["Registration.RegistrationStatus"],
        )


def read_relationships(path: Path) -> Iterator[Relationship]:
    with path.open(newline="", encoding="utf-8") as fh:
        yield from relationships(csv.DictReader(fh))
