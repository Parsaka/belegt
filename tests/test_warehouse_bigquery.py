"""The BigQuery load path, without BigQuery: schema and row encoding match the DuckDB tables."""

from datetime import date

from belegt.loaders import ets, gleif
from belegt.resolution import Match
from belegt.warehouse import _json_row, bigquery_schema


def test_schema_maps_python_types_to_bigquery_types():
    schema = {f["name"]: f["type"] for f in bigquery_schema(ets.EtsEmission)}
    assert schema["installation_id"] == "STRING"
    assert schema["year"] == "INT64"
    assert schema["verified_t"] == "INT64"
    assert all(f["mode"] == "NULLABLE" for f in bigquery_schema(Match))


def test_dates_are_sent_as_iso_text():
    rel = gleif.Relationship(
        "A", "B", "IS_DIRECTLY_CONSOLIDATED_BY", "ACTIVE", date(2018, 1, 2), None, "PUBLISHED"
    )
    row = _json_row(gleif.Relationship, rel)
    assert row["valid_from"] == "2018-01-02"
    assert row["valid_to"] is None
    assert set(row) == {f["name"] for f in bigquery_schema(gleif.Relationship)}
