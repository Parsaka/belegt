"""Extraction of E1-6 totals. Page texts are written like the tables in real statements; the real
PDFs are copyrighted and never committed."""

from belegt.documents.metrics import extract, extract_page, first_figure, metric_of, page_unit
from belegt.documents.model import Page

TABLE = """E1-6 Brutto-Scope-1-, -2- und -3-THG-Emissionen
THG-Emissionen in Mio. t CO2e 2024 2023 Veränderung in %
Scope 1 (direkte Emissionen)1 15,6 16,9 -7,7
Scope 2 marktbasiert 2,4 2,9 -17,2
Scope 2 standortbasiert 3,1 3,3 -6,1
Scope 1 und 2 (marktbasiert) 18,0 19,8 -9,1
Scope 3 gesamt 61,2 64,0 -4,4
"""
PROSE = "Unsere Scope-1-Emissionen sanken 2024. Ziel: Scope 1 bis 2030 um 25 % senken (in t CO2e)."


def test_units_from_the_table_header():
    assert page_unit(TABLE) == ("mt", "Mio. t")
    assert page_unit("in Tausend Tonnen CO2-Äquivalente") == ("kt", "Tausend Tonnen")
    assert page_unit("Emissions (t CO2e)") == ("t", "t")
    assert page_unit("Scope 1 15,6") is None


def test_rows_are_classified_and_combined_scopes_skipped():
    assert metric_of("Scope 1 (direkte Emissionen)1 15,6 16,9") == "scope1"
    assert metric_of("Scope 2 marktbasiert 2,4") == "scope2_market"
    assert metric_of("Scope 2 location-based 3.1") == "scope2_location"
    assert metric_of("Scope 1 und 2 (marktbasiert) 18,0") is None
    assert metric_of("Scope 3 Kategorie 1 eingekaufte Waren 12,0") is None
    assert metric_of("Scope 3 gesamt 61,2") == "scope3"


def test_first_figure_skips_footnotes_and_years():
    assert first_figure("Scope 1 (direkte Emissionen)1 15,6 16,9", decimal_comma=True) == "15,6"
    assert first_figure("Scope 1 2024 1.234.567 1.300.000", decimal_comma=True) == "1.234.567"
    assert first_figure("Scope 1 1,234,567 1,300,000", decimal_comma=False) == "1,234,567"


def test_table_values_in_tonnes_with_page_and_quote():
    got = {m.metric: m for m in extract_page(Page("acme-2024", 87, TABLE), decimal_comma=True)}
    assert got["scope1"].value_t == 15_600_000
    assert got["scope2_market"].value_t == 2_400_000
    assert got["scope3"].value_t == 61_200_000
    assert got["scope1"].page == 87
    assert got["scope1"].quote.startswith("Scope 1 (direkte Emissionen)")


def test_the_table_page_wins_over_a_narrative_mention():
    pages = [Page("acme-2024", 12, PROSE), Page("acme-2024", 87, TABLE)]
    selected = [m for m in extract(pages, decimal_comma=True) if m.selected]
    assert {(m.metric, m.page) for m in selected} == {
        ("scope1", 87),
        ("scope2_market", 87),
        ("scope2_location", 87),
        ("scope3", 87),
    }


def test_prose_lines_do_not_start_a_row():
    assert extract_page(Page("acme-2024", 12, PROSE), decimal_comma=True) == []
