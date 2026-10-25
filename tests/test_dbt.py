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
