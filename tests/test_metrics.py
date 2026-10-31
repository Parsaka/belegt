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
Gesamtemissionen auf Basis der standortbezogenen Scope-2-Methode Tsd. t CO2eq 40.465 46.348 -5.883 -12,7 %
Gesamtemissionen auf Basis der marktbezogenen Scope-2-Methode Tsd. t CO2eq 39.909 45.699 -5.790 -12,7 %
"""

RWE_P124 = """Scope 1, 2 and 3 emissions1 Retrospective Milestones and targets years
metric tons CO2e Base year
(2022)2
2024 2025 20303 20403 Annual %
Scope 1 GHG emissions
Gross Scope 1 GHG emissions 85,736,423 53,242,042 n. a. n. a. n. a. n. a.
Percentage of Scope 1 GHG emissions from regulated emission trading schemes 97.2 97.1 n. a. n. a. n. a. n. a.
Scope 2 GHG emissions
Gross location-based Scope2 GHG emissions 195,727 392,956 n. a. n. a. n. a. n. a.
Gross market-based Scope2 GHG emissions 195,727 392,956 n. a. n. a. n. a. n. a.
Significant Scope 3 GHG emissions
T otal gross indirect (Scope 3) GHG emissions 22,151,605 21,766,996 n. a. 12,848,724 2,215,297 5.3%
"""

HEIDELBERG_P125 = """2020 2023 2024 Einheit
Scope-1-Treibhausgasemissionen
Absolute Brutto-CO2-Emissionen (Scope 1) – 61,2 61,1 Mio t
olute Netto-CO2-Emissionen (Scope 1) – 57,1 56,9 Mio t
Scope-2-Treibhausgasemissionen
Absolute CO2-Emissionen aus externer Erzeugung von Strom
und Wärme (Scope 2) – mark
tbasierter Ansatz – 4,5 4,2 Mio t
"""

HEIDELBERG_P126_PROSE = """absoluten Emissionen für Scope 1 mit 0,49 (i. V.: 0,50)
Mio t CO2 auf dem Vorjahresniveau und in Einklang
marktbasierten Scope-2-Emissionen ergibt sich ein
leichter Rückgang auf 0,24 (i. V.: 0,25) Mio t CO2.
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
    # all scopes together, labelled by their Scope 2 method, are not Scope 2
    assert all(m.value_t not in (40_465_000, 39_909_000) for m in rows)
    location = next(m for m in rows if m.metric == "scope2_location" and m.selected)
    assert location.value_t == 1_247_000


def test_a_header_over_two_lines_with_the_base_year_first():
    rows = list(extract([Page("rwe-2024", 124, RWE_P124)], False, report_year=2024))
    selected = {m.metric: (m.value_t, m.column_year) for m in rows if m.selected}
    assert selected == {
        "scope1": (53_242_042, 2024),
        "scope2_location": (392_956, 2024),
        "scope2_market": (392_956, 2024),
        "scope3": (21_766_996, 2024),
    }


SALZGITTER_P160 = """Salzgitter AG | Geschäftsbericht 2024
2021 2023 04 2025 2030 2050
Scope-1-THG-Bruttoemissionen (Tt CO2e) 10.724 0.35 6.900
Standortbezogene Scope-2-THG-Bruttoemissionen (Tt CO2e) 366 338
"""


def test_a_running_head_is_not_a_header_and_a_garbled_header_is_uncertain():
    rows = extract_page(Page("salzgitter-2024", 160, SALZGITTER_P160), True, 2024)
    assert rows and all(m.column_year is None for m in rows)  # no readable 2024 column


def test_split_words_and_a_dash_inside_the_label():
    rows = extract_page(Page("heidelberg-materials-2024", 125, HEIDELBERG_P125), True, 2024)
    assert [(m.metric, m.value_t, m.column_year) for m in rows] == [
        ("scope1", 61_100_000, 2024),
        ("scope1", 56_900_000, 2024),
        ("scope2_market", 4_200_000, 2024),
    ]


def test_prose_with_the_prior_year_in_brackets():
    page = Page("heidelberg-materials-2024", 126, HEIDELBERG_P126_PROSE)
    assert extract_page(page, True, 2024) == []


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


THYSSENKRUPP_P123 = """THYSSENKRUPP ANNUAL REPORT 2024 / 2025
GROSS SCOPES 1, 2, 3 AND TOTAL GHG EMISSIONS
Mt CO2e 2017 / 2018 2024 / 2025 2029 / 2030 2049 / 2050
Scope 1 GHG emissions1)
Gross Scope 1 GHG emissions 24.2 19.8
Gross Scope 1 GHG emissions from regulated emission trading schemes 2) 95% 100%
Scope 2 GHG emissions1)
Gross location-based Scope 2 GHG emissions 0.9 1.1
Gross market-based Scope 2 GHG emissions 1.1 1.2
Subtotal Scope 1 and Scope 2 market-based 3) 25.3 21.0 15.6 2.5 (3.2)%
Scope 3 GHG emissions1)
Gross Scope 3 GHG emissions 3) 469.1 186.0 328.4 46.9 (2.5)%
Total GHG emissions – location-based 494.2 206.8
"""


def test_fiscal_year_columns_and_mt_units():
    rows = list(extract([Page("thyssenkrupp-2025", 123, THYSSENKRUPP_P123)], False, 2025))
    assert [(m.metric, m.value_t, m.column_year) for m in rows] == [
        ("scope1", 19_800_000, 2025),  # the 2024/2025 column, not the 2017/2018 base year
        ("scope2_location", 1_100_000, 2025),
        ("scope2_market", 1_200_000, 2025),
        ("scope3", 186_000_000, 2025),  # "Subtotal Scope 1 and Scope 2" is no row of either
    ]
    assert all(m.selected for m in rows)


def test_a_scope_3_category_is_not_the_total():
    assert metric_of("Gross Scope 3 GHG emissions category 1 purchased goods 12.0") is None


# Layouts from the dev split of the hand-labelled evaluation (evals/reported_metrics.csv)

COVESTRO_P160 = """Covestro Annual Report 2024
GHG emissions (million metric tons of CO2equivalents)1, 2
Base year3 2023 2024 Change 2030 2035 2050
Scope 1 GHG emissions
Gross Scope 1 GHG emissions 1.25 0.93 1.014 9%
Gross location-based Scope 2 GHG emissions 4.48 4.10 4.32 5%
Gross market-based Scope 2 GHG emissions 4.33 4.18 3.84 –8%
Gross Scope 3 GHG emissions 21.84 15.75 17.98 14%
"""

WACKER_P159 = """Wacker Chemie AG Annual Report 2024 159
(2020) 2023 2024
2024/2023 2025 2030 2045
Scope 1 GHG gross emissions (kt CO2e) 1,285 1,368 1,212 –11 – – – –
Location-based Scope 2
GHG gross emissions (kt CO2e) 1,579 1,368 1,311 –4 – – – –
"""

LUFTHANSA_P163 = """T058 ESRS E1-6 | AR48 GHG EMISSIONS IN 2024
(2019)
2023 2024 Change in % 2025 2030 Annual % of
Gross Scope 1 GHG emissions in 1,000 tonnes CO2e 33,349 26,822 29,159 9% n/a n/a
Gross market-based Scope 2 GHG emissions in 1,000 tonnes CO2e 200 91 49 –46% n/a n/a
"""

LANXESS_P136 = """We report Scope 1 emissions in metric tons CO2e of the consolidated companies.
Gross Scopes 1, 2, 3 and Total GHG emissions
in thousand metric tons CO2e Base year 2024 2030 2040 2050
Gross Scope 1 GHG emissions 939 854
Location-based gross Scope 2 GHG emissions 1,514 1,296
Total indirect gross (Scope 3) GHG emissions 14,745 10,372 11,000
"""

RHEINMETALL_P127 = """tonnes CO2e Retrospective Actual Milestones and target years5
20221,2 20231,2,3 20244
Gross Scope 1 GHG emissions 114,005 129,800 139,801 0.1 - - -
Gross market-based Scope 2 GHG emissions 132,821 68,896 69,897 0.0 - - -
"""


def selected(doc: str, number: int, text: str, comma: bool = False) -> dict[str, float | None]:
    rows = extract([Page(doc, number, text)], comma, report_year=2024)
    return {m.metric: m.value_t for m in rows if m.selected}


def test_a_base_year_column_without_a_year_holds_its_place():
    assert selected("covestro-2024", 160, COVESTRO_P160) == {
        "scope1": 1_014_000,
        "scope2_location": 4_320_000,
        "scope2_market": 3_840_000,
        "scope3": 17_980_000,
    }
    assert selected("lanxess-2024", 136, LANXESS_P136)["scope1"] == 854_000


def test_a_change_column_does_not_restart_the_header():
    assert selected("wacker-2024", 159, WACKER_P159) == {
        "scope1": 1_212_000,
        "scope2_location": 1_311_000,
    }


def test_column_titles_between_the_header_lines_do_not_split_the_header():
    text = WACKER_P159.replace("2024/2023 2025", "Change in %\nTargets\n2024/2023 2025")
    assert selected("wacker-2024", 159, text)["scope1"] == 1_212_000


def test_thousand_tonnes_written_as_1000_is_a_unit_not_a_column():
    assert selected("lufthansa-2024", 163, LUFTHANSA_P163) == {
        "scope1": 29_159_000,
        "scope2_market": 49_000,
    }


def test_the_unit_above_the_table_wins_over_one_in_the_prose_before_it():
    assert selected("lanxess-2024", 136, LANXESS_P136)["scope3"] == 10_372_000


def test_footnote_digits_glued_to_header_years():
    assert selected("rheinmetall-2024", 127, RHEINMETALL_P127) == {
        "scope1": 139_801,
        "scope2_market": 69_897,
    }


def test_a_group_or_sum_row_is_the_scope_3_total():
    assert metric_of("Scope-3-Emissionen EnBW-Konzern Tsd. t CO2eq 30.356 33.987") == "scope3"
    assert metric_of("Summe Scope-3-Emissionen d, e, f 18,9 21,6") == "scope3"
