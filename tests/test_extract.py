"""The extract filters, on the real golden-copy RR fixture. The downloads themselves are live."""

import csv
from pathlib import Path

import pytest

from belegt.extract import (
    LEI_COLUMNS,
    check_columns,
    consolidation_parents,
    latest_verified_emissions,
    select_eea,
    select_entities,
    select_relationships,
    write_csv,
)

FIXTURES = Path(__file__).parent / "fixtures"
BASF = "529900PM64WH8AF1E917"


def rows(name: str) -> list[dict[str, str]]:
    with (FIXTURES / name).open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_latest_verified_emissions_picks_the_newest_year():
    links = [
        "https://x/document/download/a_en?filename=verified_emissions_2023_en.xlsx",
        "https://x/files/verified_emissions_2025_en.xlsx",
        "https://x/files/verified_emissions_2024_en.xlsx",
        "https://x/files/policy_ets_registry_operators_ets_en.xlsx",
    ]
    assert latest_verified_emissions(links).endswith("verified_emissions_2025_en.xlsx")


def test_latest_verified_emissions_fails_loudly_when_the_page_changes():
    with pytest.raises(ValueError, match="no verified_emissions"):
        latest_verified_emissions(["https://x/other.xlsx"])


def test_consolidation_parents_ignore_branch_relations():
    rr = rows("gleif_rr.csv")
    parents = consolidation_parents(rr)
    assert BASF in parents
    branch_parents = {
        r["Relationship.EndNode.NodeID"]
        for r in rr
        if r["Relationship.RelationshipType"] == "IS_INTERNATIONAL_BRANCH_OF"
    }
    only_branch = branch_parents - {
        r["Relationship.EndNode.NodeID"]
        for r in rr
        if r["Relationship.RelationshipType"] != "IS_INTERNATIONAL_BRANCH_OF"
    }
    assert not only_branch & parents


def test_select_relationships_keeps_consolidation_edges_of_kept_children():
    rr = rows("gleif_rr.csv")
    child = rr[0]["Relationship.StartNode.NodeID"]
    kept = list(select_relationships(rr, {child}))
    assert kept
    assert {r["Relationship.StartNode.NodeID"] for r in kept} == {child}
    assert not any("Qualifiers" in k or "Quantifiers" in k for k in kept[0])


def test_select_entities_keeps_germans_and_foreign_parents():
    def row(lei: str, country: str) -> dict[str, str]:
        return {c: "" for c in LEI_COLUMNS} | {
            "LEI": lei,
            "Entity.LegalAddress.Country": country,
            "Extra.Column": "dropped",
        }

    picked = list(select_entities([row("DE1", "DE"), row("FR1", "FR"), row("US1", "US")], {"US1"}))
    assert [r["LEI"] for r in picked] == ["DE1", "US1"]
    assert set(picked[0]) == set(LEI_COLUMNS)


def test_check_columns_names_what_is_missing():
    with pytest.raises(ValueError, match=r"Entity\.LegalName"):
        check_columns(["LEI"], LEI_COLUMNS, "GLEIF")


def test_select_eea_follows_ets_ids_to_facilities():
    ets_ids = rows("eea_ets_identifiers.csv")
    installations = rows("eea_installations.csv")
    facilities = rows("eea_facilities.csv")
    foreign = dict(ets_ids[0], ETSIdentifier="AT000000000000001")
    links, inst, fac = select_eea([*ets_ids, foreign], installations, facilities)
    assert len(links) == len(ets_ids)
    assert {r["Installation_INSPIRE_ID"] for r in inst} <= {
        r["Installation_INSPIRE_ID"] for r in links
    }
    assert {r["Facility_INSPIRE_ID"] for r in fac} <= {
        r["Parent_Facility_INSPIRE_ID"] for r in inst
    }


def test_write_csv_round_trips(tmp_path):
    rr = rows("gleif_rr.csv")[:3]
    assert write_csv(tmp_path / "x.csv", rr) == 3
    with (tmp_path / "x.csv").open(newline="", encoding="utf-8") as fh:
        assert list(csv.DictReader(fh)) == rr


def test_only_real_pdfs_count_as_the_esrs_download():
    from belegt.extract import is_pdf

    assert is_pdf(b"%PDF-1.7")
    assert not is_pdf(b"<!DOCTYPE html>")
