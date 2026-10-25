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


# Short table lines as pypdf reads them from real 2024 statements (factual rows, quoted with the
# page; the PDFs themselves are never committed). Each case broke a simpler extractor.

ENBW_P159 = """Einheit 2024 2023 1
Scope-1-THG-Bruttoemissionen
CO2-Emissionen aus Verbrennung und Abbau von Biomasse Tsd. t CO2eq 495 490 5 1,0 %
Anteil aus regulierten Emissionshandelssystemen % 94 92 2 2,2
Scope-1-Emissionen aus Stromerzeugung nicht beeinflussbar 2 Tsd. t CO2eq 1.592 2.558 -966 -37,8 %
Scope-1-Emissionen aus Wärmeerzeugung Tsd. t CO2eq 669 676 -7 -1,0 %
Scope-1-Emissionen EnBW-Konzern 4 Tsd. t CO2eq 8.862 10.923 -2.061 -18,9 %
Standortbezogene Scope-2-THG-Bruttoemissionen Tsd. t CO2eq 1.247 1.438 -191 -13,3 %
Marktbezogene Scope-2-THG-Bruttoemissionen Tsd. t CO2eq 691 789 -98 -12,4 %
"""

RWE_P125 = """Scope 1 emissions attributable to the consolidated accounting group (the parent and
subsidiaries) amounted to 53,242,042 metric tons of CO2e in 2024.
Scope 1 GHG emissions Unit 2024
(3) Flexible Generation million metric
tons CO2e 15.1
Core business – total Scope 1 GHG emissions million metric
tons CO2e 15.1
(5) Phaseout Technologies million metric
tons CO2e 38.1
Total RWE Group Scope 1 emissions million metric
tons CO2e 53.2
"""

HEIDELBERG_P126 = """2023 2024 Einheit
Scope-1-Treibhausgasemissionen
Absolute CO2-Emissionen aus Brennstoffen (Scope 1)1) 0,50 0,49 Mio t
Spezifische CO2-Emissionen aus Brennstoffen (Scope 1) 1) 1,85 1,90 kg CO2 / t
"""

ENBW_P154_TARGETS = """Einheit 2030 2035
Scope 1 Mio. t CO2eq – – 16,6
Scope 1 % -70 bis -75 -83 –
"""


def test_the_group_total_row_wins_in_its_unit():
    rows = list(extract([Page("enbw-2024", 159, ENBW_P159)], True, report_year=2024))
    scope1 = next(m for m in rows if m.metric == "scope1" and m.selected)
    assert scope1.value_t == 8_862_000  # "Konzern", Tsd. t, the 2024 column
    assert scope1.column_year == 2024
    assert scope1.quote.startswith("Scope-1-Emissionen EnBW-Konzern")
    market = next(m for m in rows if m.metric == "scope2_market" and m.selected)
    assert market.value_t == 691_000
    # biomass CO2 and the share from emission trading are not Scope 1 totals
    assert all(m.value_t != 495_000 and m.value_t != 94_000 for m in rows)


def test_a_wrapped_row_and_prose_with_a_figure():
    rows = list(extract([Page("rwe-2024", 125, RWE_P125)], False, report_year=2024))
    scope1 = next(m for m in rows if m.selected)
    assert scope1.value_t == 53_200_000
    assert scope1.unit_raw.lower().startswith("million metric")
    assert scope1.column_year == 2024


def test_the_reporting_year_column_when_the_prior_year_comes_first():
    rows = extract_page(Page("heidelberg-materials-2024", 126, HEIDELBERG_P126), True, 2024)
    assert [(m.metric, m.value_t, m.column_year) for m in rows] == [("scope1", 490_000, 2024)]


def test_target_tables_yield_no_reporting_year_figure():
    rows = extract_page(Page("enbw-2024", 154, ENBW_P154_TARGETS), True, 2024)
    assert all(m.column_year is None for m in rows)  # no 2024 column: uncertain at best
    assert all(m.value_t != 70_000_000 for m in rows)  # a percentage target is not a total
