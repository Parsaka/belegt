import pytest

from belegt.loaders.gleif import LegalEntity
from belegt.resolution import normalise, resolve, score


def entity(lei, name, city="Ludwigshafen am Rhein", status="ACTIVE"):
    return LegalEntity(lei, name, "DE", city, None, None, None, status, "ISSUED", "2026-01-01")


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("BASF SE", "basf"),
        ("Heidelberg Materials AG", "heidelberg materials"),
        ("RWE Power Aktiengesellschaft", "rwe power"),
        ("Müller GmbH & Co. KG", "mueller"),
        ("Straßenbau Süd GmbH", "strassenbau sued"),
    ],
)
def test_normalise(raw, expected):
    assert normalise(raw) == expected


def test_legal_form_variants_are_equal():
    assert score("RWE Power AG", "RWE Power Aktiengesellschaft") == 1.0


def test_exact_match_is_accepted():
    m = resolve(
        "BASF SE",
        "Ludwigshafen",
        [entity("529900PM64WH8AF1E917", "BASF SE"), entity("X", "BASF Coatings GmbH")],
    )
    assert m.decision == "accepted" and m.lei == "529900PM64WH8AF1E917"


def test_partial_match_goes_to_review():
    m = resolve("BASF Schwarzheide", None, [entity("Y", "BASF Schwarzheide Chemie GmbH")])
    assert m.decision == "review"


def test_no_candidate_is_unmatched():
    m = resolve("Stadtwerke Musterstadt", None, [entity("Z", "BASF SE")])
    assert m.decision == "unmatched" and m.lei is None


def test_inactive_entity_loses_to_active():
    m = resolve(
        "Example AG",
        None,
        [entity("OLD", "Example AG", status="INACTIVE"), entity("NEW", "Example AG")],
    )
    assert m.lei == "NEW"


def test_registry_lei_with_dashes_is_normalised():
    from belegt.resolution import normalise_lei

    assert normalise_lei("5299-00RVRNBYTWP2VG-82") == "529900RVRNBYTWP2VG82"
    assert normalise_lei("not a lei") is None


@pytest.mark.parametrize(("raw", "expected"), [("HRB 6000", "HRB 6000"), ("hrb6000", "HRB 6000"), ("Amtsgericht Essen HRB 14525", "HRB 14525"), ("FN 87132 k", "FN 87132K"), ("", None)])
def test_normalise_register(raw, expected):
    from belegt.resolution import normalise_register

    assert normalise_register(raw) == expected


def test_operator_resolution_prefers_registry_lei():
    from belegt.resolution import resolve_operator

    basf = LegalEntity("529900PM64WH8AF1E917", "BASF SE", "DE", "Ludwigshafen am Rhein", "HRB 6000", None, None, "ACTIVE", "ISSUED", "x")
    m = resolve_operator("BASF Aktiengesellschaft (alt)", "5299-00PM64WH8AF1-E917", None, None, [basf])
    assert m.decision == "accepted" and m.lei == basf.lei and "LEI" in m.evidence


def test_operator_resolution_by_register_number_needs_a_plausible_name():
    from belegt.resolution import resolve_operator

    basf = LegalEntity("529900PM64WH8AF1E917", "BASF SE", "DE", None, "HRB 6000", None, None, "ACTIVE", "ISSUED", "x")
    assert resolve_operator("BASF SE", None, "HRB 6000", None, [basf]).decision == "accepted"
    assert resolve_operator("Stadtwerke Beispiel GmbH", None, "HRB 6000", None, [basf]).decision == "review"
