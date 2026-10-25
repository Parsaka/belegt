"""Runs the dbt project on the real fixtures, then proves the SCD2 snapshot opens a new version."""

from pathlib import Path

import pytest

dbt_main = pytest.importorskip("dbt.cli.main")
duckdb = pytest.importorskip("duckdb")

from belegt.warehouse import load_directory  # noqa: E402

ROOT = Path(__file__).parents[1]
FIXTURES = ROOT / "tests" / "fixtures"
PROJECT = ROOT / "dbt"


def dbt(*args: str) -> None:
    result = dbt_main.dbtRunner().invoke(
        [*args, "--project-dir", str(PROJECT), "--profiles-dir", str(PROJECT)]
    )
    assert result.success, result.exception


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory, monkeypatch_module):
    db = tmp_path_factory.mktemp("wh") / "belegt.duckdb"
    load_directory(FIXTURES, db)
    monkeypatch_module.setenv("BELEGT_DUCKDB", str(db))
    dbt("build")
    return db


@pytest.fixture(scope="module")
def monkeypatch_module():
    mp = pytest.MonkeyPatch()
    yield mp
    mp.undo()


def query(db: Path, sql: str) -> list[tuple]:
    con = duckdb.connect(str(db))
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_every_registry_installation_is_in_the_dimension(warehouse):
    (raw,) = query(warehouse, "select count(distinct installation_id) from raw.ets_emissions")[0]
    (dim,) = query(warehouse, "select count(*) from marts.dim_installation")[0]
    assert raw == dim > 0


def test_unreported_years_are_null_not_zero(warehouse):
    rows = query(
        warehouse,
        "select count(*) from marts.fct_verified_emissions where status = 'n/a' and verified_t is not null",
    )
    assert rows == [(0,)]


def test_snapshot_opens_a_new_version_on_change(warehouse):
    con = duckdb.connect(str(warehouse))
    lei = con.execute("select lei from raw.gleif_entities order by lei limit 1").fetchone()[0]
    # Synthetic change for the test only: GLEIF republishes the record with a new address.
    con.execute(
        "update raw.gleif_entities set city = 'Teststadt', last_update = '2099-01-01T00:00:00Z' where lei = ?",
        [lei],
    )
    con.close()
    dbt("snapshot")
    dbt("run", "--select", "dim_legal_entity")
    versions = query(
        warehouse,
        f"select city, is_current from marts.dim_legal_entity where lei = '{lei}' order by valid_from",
    )
    assert len(versions) == 2
    assert versions[-1] == ("Teststadt", True)
    assert versions[0][1] is False


def test_scope1_consistency_flags_ets_above_the_reported_figure(warehouse):
    # Synthetic extracted figures for the test only; real ones come from `belegt reports`.
    con = duckdb.connect(str(warehouse))
    con.execute(
        """insert into raw.reported_metrics values
        ('basf-2024', 'scope1', 1000000.0, 3, 'Mio. t', 'Scope 1 1,0 1,1', 3, true),
        ('basf-2024', 'scope1', 2.0, 9, 't', 'Scope 1 2 3', 1, false),
        ('rwe-2024', 'scope1', 60000000.0, 5, 'Mio. t', 'Scope 1 60,0 70,0', 3, true),
        ('thyssenkrupp-2024', 'scope3', 5.0, 4, 'Mio. t', 'Scope 3 gesamt 5 6', 3, true)"""
    )
    con.close()
    dbt("build", "--select", "stg_reported_metrics+")
    rows = dict(
        (r[0], r[1:])
        for r in query(
            warehouse,
            "select doc_id, status, reported_page, caveat from marts.mart_scope1_consistency",
        )
    )
    # the fixture holds 1.52 Mt verified for BASF's German installations in 2024
    assert rows["basf-2024"] == ("ets_exceeds_reported", 3, None)
    assert rows["rwe-2024"][0] == "no_ets_group"  # RWE's installations are not in the fixtures
    assert rows["thyssenkrupp-2024"][0] == "no_reported_figure"
    assert "09-30" in rows["thyssenkrupp-2024"][2]
