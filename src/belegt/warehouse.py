"""Load parsed sources into the raw tables of DuckDB (local and CI) or BigQuery (cloud).

Both targets get the same rows and column types, so dbt runs the same models on either.
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

from belegt.documents.metrics import ReportedMetric
from belegt.documents.reports import read_metrics
from belegt.loaders import eea, ets, gleif
from belegt.resolution import CandidateIndex, Match, resolve, resolve_operator

_SQL_TYPES = {str: "VARCHAR", int: "BIGINT", float: "DOUBLE", bool: "BOOLEAN", date: "DATE"}


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
    """API records (JSON, the fixtures) or golden-copy rows (CSV, a full extract)."""
    seen: dict[str, gleif.LegalEntity] = {}
    for path in paths:
        if path.suffix == ".csv":
            found: Iterable[gleif.LegalEntity] = gleif.read_entities(path)
        else:
            payload = json.loads(path.read_text())
            records = (
                payload if isinstance(payload, list) else [r for v in payload.values() for r in v]
            )
            found = (gleif.entity_from_api(record) for record in records)
        for entity in found:
            seen[entity.lei] = entity
    return list(seen.values())


Table = tuple[type[Any], Iterable[Any]]


def parse_directory(source: Path) -> dict[str, Table]:
    """Every raw table as (row dataclass, rows), plus the entity matches computed from them."""
    facilities = list(eea.read_facilities(source / "eea_facilities.csv"))
    operators = list(ets.read_operators(source / "ets_operators_de.xlsx"))
    entities = _entities(
        [p for p in sorted(source.glob("gleif_entities*")) if p.suffix in {".json", ".csv"}]
    )
    tables: dict[str, Table] = {
        "ets_emissions": (
            ets.EtsEmission,
            ets.read_verified_emissions(source / "ets_verified_emissions_de.xlsx"),
        ),
        "ets_operators": (ets.Operator, operators),
        "eea_ets_links": (eea.EtsLink, eea.read_ets_links(source / "eea_ets_identifiers.csv")),
        "eea_installations": (
            eea.Installation,
            eea.read_installations(source / "eea_installations.csv"),
        ),
        "eea_facilities": (eea.Facility, facilities),
        "gleif_entities": (gleif.LegalEntity, entities),
        "gleif_relationships": (
            gleif.Relationship,
            gleif.read_relationships(source / "gleif_rr.csv"),
        ),
        # Written by `belegt reports`; an empty table until the first report run.
        "reported_metrics": (
            ReportedMetric,
            read_metrics(sorted((source / "reports" / "metrics").glob("*.jsonl"))),
        ),
    }
    # One decision per name: operators from the registry first, EEA parent names add the rest.
    index = CandidateIndex(entities)
    by_lei = {e.lei: e for e in entities}
    matches: dict[str, Match] = {}
    for op in operators:
        if op.account_holder not in matches:
            pool = index.candidates(op.account_holder, op.register_nr)
            matches[op.account_holder] = resolve_operator(
                op.account_holder, op.lei, op.register_nr, op.city, pool, by_lei
            )
    for f in facilities:
        name = f.parent_company_name
        if name and name not in matches:
            matches[name] = resolve(name, f.city, index.candidates(name))
    tables["entity_matches"] = (Match, matches.values())
    return tables


def load_directory(source: Path, db_path: Path) -> dict[str, int]:
    """Replace the raw tables in a local DuckDB file (local runs and CI)."""
    import duckdb

    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_path))
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    counts = {
        name: write_table(con, name, cls, rows)
        for name, (cls, rows) in parse_directory(source).items()
    }
    con.close()
    return counts


_BQ_TYPES = {
    "VARCHAR": "STRING",
    "BIGINT": "INT64",
    "DOUBLE": "FLOAT64",
    "BOOLEAN": "BOOL",
    "DATE": "DATE",
}


def bigquery_schema(cls: type[Any]) -> list[dict[str, str]]:
    """BigQuery schema from a row dataclass; the same types as the DuckDB tables."""
    hints = typing.get_type_hints(cls)
    return [
        {"name": f.name, "type": _BQ_TYPES[_sql_type(hints[f.name])], "mode": "NULLABLE"}
        for f in dataclasses.fields(cls)
    ]


def _json_row(cls: type[Any], row: Any) -> dict[str, Any]:
    return {
        f.name: v.isoformat() if isinstance(v := getattr(row, f.name), date) else v
        for f in dataclasses.fields(cls)
    }


def load_bigquery(source: Path, project: str, dataset: str = "raw") -> dict[str, int]:
    """Replace the raw tables in BigQuery with load jobs (free; queries are what is billed).

    WRITE_TRUNCATE makes every load idempotent. Credentials come from the environment: the
    workload identity of the GitHub Actions run, never a key file.
    """
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    counts: dict[str, int] = {}
    for name, (cls, rows) in parse_directory(source).items():
        data = [_json_row(cls, r) for r in rows]
        config = bigquery.LoadJobConfig(
            schema=[bigquery.SchemaField.from_api_repr(f) for f in bigquery_schema(cls)],
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
            source_format=bigquery.SourceFormat.NEWLINE_DELIMITED_JSON,
        )
        job = client.load_table_from_json(data, f"{project}.{dataset}.{name}", job_config=config)
        job.result()
        counts[name] = len(data)
    return counts
