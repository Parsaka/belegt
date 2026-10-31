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


def test_esrs_falls_back_through_its_sources_and_is_optional(tmp_path):
    from contextlib import contextmanager

    from belegt import extract

    class Response:
        def __init__(self, body):
            self.body = body

        def raise_for_status(self):
            if self.body is None:
                raise RuntimeError("403")

        def iter_bytes(self, size):
            yield self.body

    class Client:
        def __init__(self, bodies):
            self.bodies = bodies
            self.headers = []

        @contextmanager
        def stream(self, method, url, **kwargs):
            self.headers.append(kwargs.get("headers", {}))
            yield Response(self.bodies[len(self.headers) - 1])

    found = extract.extract_esrs(Client([None, b"<html>challenge</html>", b"%PDF-1.7 x"]), tmp_path)
    assert [f.file for f in found] == ["esrs_de.pdf"]
    assert (tmp_path / "esrs_de.pdf").read_bytes().startswith(b"%PDF")

    empty = tmp_path / "none"
    empty.mkdir()
    client = Client([None, b"<html>", b"<html>"])
    assert extract.extract_esrs(client, empty) == []  # the run goes on without the ESRS
    assert not (empty / "esrs_de.pdf").exists()
    assert client.headers[0]["Accept"] == "application/pdf"  # content negotiation on the ELI


def test_postcodes_are_written_unchanged_from_the_zip(tmp_path):
    import io
    import zipfile
    from contextlib import contextmanager

    from belegt import extract

    text = "\t".join(["DE", "01067", "Dresden", "Sachsen", "SN", "", "00", "Dresden", "14612"])
    line = (text + "\t51.0587\t13.7174\t4\n").encode()
    blob = io.BytesIO()
    with zipfile.ZipFile(blob, "w") as z:
        z.writestr("DE.txt", line)
        z.writestr("readme.txt", "GeoNames readme")

    class Response:
        def raise_for_status(self):
            pass

        def iter_bytes(self, size):
            yield blob.getvalue()

    class Client:
        @contextmanager
        def stream(self, method, url, **kwargs):
            yield Response()

    work = tmp_path / "work"
    work.mkdir()
    (found,) = extract.extract_postcodes(Client(), tmp_path, work)
    assert (found.file, found.rows) == ("geonames_postcodes_de.txt", 1)
    assert (tmp_path / "geonames_postcodes_de.txt").read_bytes() == line
