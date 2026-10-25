"""Load parsed sources into the raw schema of a local DuckDB file (CI and local dbt runs).

In the cloud the same rows go to BigQuery load jobs; dbt then runs the same models on either.
Every load replaces its table, so re-runs are idempotent.
"""

from __future__ import annotations

import dataclasses
import json
import types
import typing
from collections.abc import Iterable, Sequence
from datetime import date
from pathlib import Path
from typing import Any

from belegt.loaders import eea, ets, gleif
from belegt.resolution import Match, resolve

_SQL_TYPES = {str: "VARCHAR", int: "BIGINT", float: "DOUBLE", date: "DATE"}


def _sql_type(annotation: Any) -> str:
    args = [a for a in typing.get_args(annotation) if a is not type(None)]
    base = args[0] if isinstance(annotation, types.UnionType) and args else annotation
    return _SQL_TYPES[base]


def write_table(con: Any, name: str, cls: type[Any], rows: Iterable[Any]) -> int:
    fields = dataclasses.fields(cls)
    hints = typing.get_type_hints(cls)
    columns = ", ".join(f"{f.name} {_sql_type(hints[f.name])}" for f in fields)
    con.execute(f"CREATE OR REPLACE TABLE raw.{name} ({columns})")
    data = [tuple(getattr(r, f.name) for f in fields) for r in rows]
    if data:
        marks = ", ".join("?" for _ in fields)
        con.executemany(f"INSERT INTO raw.{name} VALUES ({marks})", data)
    return len(data)


def _entities(paths: Sequence[Path]) -> list[gleif.LegalEntity]:
    seen: dict[str, gleif.LegalEntity] = {}
    for path in paths:
        payload = json.loads(path.read_text())
        records = payload if isinstance(payload, list) else [r for v in payload.values() for r in v]
        for record in records:
            entity = gleif.entity_from_api(record)
            seen[entity.lei] = entity
    return list(seen.values())


def load_directory(source: Path, db_path: Path) -> dict[str, int]:
    import duckdb

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    facilities = list(eea.read_facilities(source / "eea_facilities.csv"))
    entities = _entities(sorted(source.glob("gleif_entities*.json")))
    counts = {
        "ets_emissions": write_table(
            con, "ets_emissions", ets.EtsEmission,
            ets.read_verified_emissions(source / "ets_verified_emissions_de.xlsx"),
        ),
        "eea_ets_links": write_table(
            con, "eea_ets_links", eea.EtsLink,
            eea.read_ets_links(source / "eea_ets_identifiers.csv"),
        ),
        "eea_installations": write_table(
            con, "eea_installations", eea.Installation,
            eea.read_installations(source / "eea_installations.csv"),
        ),
        "eea_facilities": write_table(con, "eea_facilities", eea.Facility, facilities),
        "gleif_entities": write_table(con, "gleif_entities", gleif.LegalEntity, entities),
        "gleif_relationships": write_table(
            con, "gleif_relationships", gleif.Relationship,
            gleif.read_relationships(source / "gleif_rr.csv"),
        ),
    }  # fmt: skip
    by_name: dict[str, str | None] = {}
    for f in facilities:
        if f.parent_company_name:
            by_name.setdefault(f.parent_company_name, f.city)
    matches = [resolve(name, city, entities) for name, city in sorted(by_name.items())]
    counts["entity_matches"] = write_table(con, "entity_matches", Match, matches)
    con.close()
    return counts
