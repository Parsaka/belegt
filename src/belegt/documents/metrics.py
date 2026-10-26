"""Greenhouse-gas totals from sustainability statements, each with the page it came from.

The ESRS E1-6 figures sit in a table, but every report lays it out differently. The rules
below come from the real statements in `dbt/seeds/reports.csv` (see the Reports workflow's
probe output); each one is a case that broke a simpler version:

1. **Rows.** A row starts with a scope label (Scope 1; Scope 2 market- or location-based;
   Scope 3 total) within its first 60 characters. Combined scopes ("Scope 1 und 2") are
   skipped, and so are the all-scope totals that name their Scope 2 method ("Gesamtemissionen
   auf Basis der marktbezogenen Scope-2-Methode"). A label line without figures takes the next
   line as its continuation, because PDF text often wraps "million metric / tons CO2e 53.2".
   Keywords are matched with spaces removed, since PDF text splits words ("mark tbasierter").
2. **Units.** The row's own unit ("Tsd. t CO2eq", "Mio t", "Tt CO2e", "million metric tons")
   wins over the first CO2 unit on the page. A page without any unit yields nothing. Rows of
   intensities (per tonne, per MWh, per EUR), percentages and shares are not totals.
3. **Columns.** The last line above the row that lists years is the column header; two such
   lines in a row are one header ("Base year (2022)" / "2024 2025 2030"), and a footnote digit
   glued to a year ("20303") is dropped. A line with one year is a header only if the year is
   bracketed or the line names the unit column, so a running head ("Geschäftsbericht 2024") is
   not. The figure is taken from the reporting year's column;
   some reports put the prior year or the base year first. Dashes and "n/a" hold their column,
   but only after the label's last word: a dash inside the label is not a column. Footnote
   digits between the label and the first figure are dropped. Without a header that has the
   reporting year, the first figure is taken and `column_year` stays empty, which marks the
   figure as less certain.
4. **Choice.** Prose has many words after its figure, or a prior-year figure in brackets
   ("0,24 (i. V.: 0,25)"), and is not a row. Per metric, the figure is selected from the page
   with the most scope rows (at least two: the E1-6 table lists the scopes together),
   preferring a header with the reporting year; on that page a row that says total, group or
   gross ("gesamt", "Konzern", "Brutto") wins, then the largest value, since the parts of a
   breakdown are smaller than their sum.

Every candidate keeps its table line, so a person can check it against the page; a reviewed
correction goes to the `reported_overrides` seed, never into this code.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, replace
from decimal import Decimal

from belegt.documents.model import Page
from belegt.units import UnitError, parse_number, to_tonnes

METRICS = ("scope1", "scope2_market", "scope2_location", "scope3")
MIN_TABLE_ROWS = 2

_CO2 = r"\s*(?:of\s+)?(?:CO2|CO₂|CO 2)"
_UNIT_PATTERNS: tuple[tuple[str, str], ...] = (
    (
        "mt",
        r"Mio\.?\s*t\b|Millionen\s+(?:metrische\s+)?Tonnen|million\s+(?:metric\s+)?(?:tonnes|tons|t)\b",
    ),
    (
        "kt",
        r"Tsd\.?\s*t\b|Tt\b|kt\b|Tausend\s+(?:metrische\s+)?Tonnen|thousand\s+(?:metric\s+)?(?:tonnes|tons|t)\b",
    ),
    ("t", r"(?:metric\s+)?(?:tonnes|tons)\b|Tonnen\b|t(?=" + _CO2 + r")"),
)
_ROW_UNIT = re.compile(
    "|".join(f"(?P<{key}>(?<![\\w.]){pattern})" for key, pattern in _UNIT_PATTERNS), re.I
)
_PAGE_UNIT = re.compile(
    "|".join(f"(?P<{key}>(?<![\\w.])(?:{pattern}){_CO2})" for key, pattern in _UNIT_PATTERNS),
    re.I,
)
_SCOPE = re.compile(r"\bScope[\s-]*(?P<n>[123])\b(?!\s*(?:\+|und|and|&|/|,)\s*-?[123]\b)", re.I)
# Matched against the line without spaces: PDF text splits words ("mark tbasierter", "T otal")
_MARKET = re.compile(r"marktbasiert|marktbezogen|market-?based", re.I)
_LOCATION = re.compile(r"orts?basiert|standortbezogen|location-?based|site-?based", re.I)
_TOTAL = re.compile(r"gesamt|insgesamt|total", re.I)
# All scopes together, labelled by their Scope 2 method ("Gesamtemissionen auf Basis der
# standortbezogenen Scope-2-Methode"): not a Scope 2 figure
_ALL_SCOPES = re.compile(r"gesamtemissionen|totalghgemissions|totalemissions", re.I)
# A figure in running text gives the prior year in brackets: "0,24 (i. V.: 0,25)"
_PRIOR_YEAR = re.compile(r"\(\s*(?:i\.\s*V\.|Vorjahr|prior year|previous year)", re.I)
_GROUP_TOTAL = re.compile(r"gesamt|insgesamt|total|konzern|group|brutto|gross", re.I)
_INTENSITY = (
    r"(?:/|\bper\b|\bje\b|\bpro\b)\s*(?:t\b|tonne|MWh|kWh|€|EUR|Mio|million|net)|\bk?g\s*CO"
)
_NOT_A_TOTAL = re.compile(
    r"%|prozent|anteil|\bshare\b|percentage|spezifisch|specific|intensit|biogen|biomass|"
    + _INTENSITY,
    re.I,
)
_INTENSITY_AFTER = re.compile(_INTENSITY, re.I)  # "1,85 1,90 kg CO2 / t" after the figures
# 12.345,6 or 12,3 (German); 12,345.6 or 12.3 (English); dashes and n/a hold a column
_NUMBER = {
    True: r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?",
    False: r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?",
}
_PLACEHOLDER = "[\u2013\u2014-]" + r"(?=\s|$)|n\s*/\s*a\b|n\.\s*a\.|<\s*\d+"
_YEAR = re.compile(r"^(?:19|20)\d{2}$")
_WORD = re.compile(r"[A-Za-zÄÖÜäöüß]{2,}")


@dataclass(frozen=True)
class ReportedMetric:
    doc_id: str
    metric: str
    value_t: float | None
    page: int
    unit_raw: str
    quote: str  # the table line, at most 200 characters
    rows_on_page: int  # scope rows found on the same page; the E1-6 table has the most
    selected: bool = False
    column_year: int | None = None  # the header year of the figure's column, if found


@dataclass(frozen=True)
class _Token:
    text: str
    start: int
    is_number: bool


_TOKEN = {
    comma: re.compile(rf"(?<![\w.,/])(?:(?P<n>{number})|(?P<p>{_PLACEHOLDER}))(?![\w.,])")
    for comma, number in _NUMBER.items()
}


def _tokens(text: str, decimal_comma: bool) -> list[_Token]:
    """Numbers and column placeholders; a percentage is neither (it is a change or a share)."""
    return [
        _Token(m.group(0), m.start(), m.group("n") is not None)
        for m in _TOKEN[decimal_comma].finditer(text)
        if not re.match(r"\s*%", text[m.end() :])
    ]


def _unit_key(match: re.Match[str]) -> str:
    return next(key for key in ("mt", "kt", "t") if match.group(key))


def page_unit(text: str) -> tuple[str, str] | None:
    """(canonical unit, as written) for the first CO2 unit on the page."""
    match = _PAGE_UNIT.search(text)
    if match is None:
        return None
    return _unit_key(match), re.sub(_CO2 + r".*$", "", match.group(0), flags=re.I).strip()


def _label(line: str) -> re.Match[str] | None:
    """The scope label that starts a row, not one in the middle of prose."""
    match = _SCOPE.search(line)
    return match if match is not None and match.start() <= 60 else None


def metric_of(line: str) -> str | None:
    match = _label(line)
    if match is None:
        return None
    compact = re.sub(r"\s+", "", line)
    if _ALL_SCOPES.search(re.sub(r"\s+", "", line[: match.start()])):
        return None
    n = match.group("n")
    if n == "1":
        return "scope1"
    if n == "2":
        if _MARKET.search(compact):
            return "scope2_market"
        if _LOCATION.search(compact):
            return "scope2_location"
        return None
    return "scope3" if _TOTAL.search(compact) else None


def _values(line: str, decimal_comma: bool) -> list[_Token]:
    """The row's column values after its label: years and leading footnote digits removed."""
    label = _SCOPE.search(line)
    offset = label.end() if label else 0
    rest = line[offset:]
    found = [t for t in _tokens(rest, decimal_comma) if not _YEAR.match(t.text)]
    while found and found[0].is_number and re.fullmatch(r"\d", found[0].text):
        if len(found) > 1 or not _ROW_UNIT.search(rest):
            found = found[1:]  # a footnote marker such as "Scope 1 (direkt)1 15,6"
        else:
            break
    first = next((t for t in found if t.is_number), None)
    if first is not None:
        # A dash inside the label ("(Scope 2) - marktbasierter Ansatz - 4,5") is not a column:
        # the columns start after the label's last word
        words = list(_WORD.finditer(rest, 0, first.start))
        if words:
            found = [t for t in found if t.start >= words[-1].end()]
    return found


def figures(line: str, decimal_comma: bool) -> list[str]:
    return [t.text for t in _values(line, decimal_comma) if t.is_number]


def first_figure(line: str, decimal_comma: bool) -> str | None:
    found = figures(line, decimal_comma)
    return found[0] if found else None


def _years(line: str) -> list[int] | None:
    """The column years of a header line ("Einheit 2024 2023", "Scope 1 ... Unit 2024")."""
    line = re.sub(r"(?<![\d.,])((?:19|20)\d{2})\d(?![\d.,])", r"\1", line)  # footnote: "20303"
    years = [int(y) for y in re.findall(r"(?<!\d)(?:19|20)\d{2}(?!\d)", line)]
    if not years:
        return None
    others = [t for t in _tokens(line, False) if t.is_number and not _YEAR.match(t.text)]
    has_unit_column = re.search(r"\b(?:Einheit|Unit)\b", line, re.I) is not None
    short = len(_WORD.findall(line)) <= 6 and not _SCOPE.search(line)
    # One year alone is a running head ("Geschäftsbericht 2024") unless it is bracketed, as a
    # base year column is ("(2022)"), or the line names the unit column
    single = len(years) == 1 and not has_unit_column and not re.search(r"\(\s*\d{4}\s*\)", line)
    if single or len(others) > 1:
        return None
    return years if short or has_unit_column else None


def _continues(line: str, decimal_comma: bool) -> bool:
    """A wrapped row's second half: at most a few words (the unit) before its figures."""
    values = [t for t in _tokens(line, decimal_comma) if t.is_number and not _YEAR.match(t.text)]
    if not values or _SCOPE.search(line):
        return False
    return len(_WORD.findall(line[: values[0].start])) <= 3


def _is_prose(line: str, values: list[_Token]) -> bool:
    first = next((t for t in values if t.is_number), None)
    if first is None:
        return True
    tail = line[line.find(first.text) :]
    tail = _ROW_UNIT.sub(" ", tail)
    if _PRIOR_YEAR.search(tail):
        return True
    return len(_WORD.findall(re.sub(_CO2, " ", tail, flags=re.I))) > 3


def _rows(text: str, decimal_comma: bool) -> Iterator[tuple[str, list[int] | None]]:
    """(row line, header years above it), joining a label line with its continuation."""
    lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
    header: list[int] | None = None
    header_line = -2
    i = 0
    while i < len(lines):
        line = lines[i]
        years = _years(line)
        if years is not None:
            # A header split over lines ("Base year (2022)" / "2024 2025 2030") is one header
            follows = header and header_line == i - 1 and max(header) < years[0]
            header = header + years if header and follows else years
            header_line = i
        if _label(line) is not None:
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            if not figures(line, decimal_comma) and _continues(nxt, decimal_comma):
                line = f"{line} {nxt}"
                i += 1
            yield line, header
        i += 1


def extract_page(
    page: Page, decimal_comma: bool, report_year: int | None = None
) -> list[ReportedMetric]:
    fallback = page_unit(page.text)
    if fallback is None and not _ROW_UNIT.search(page.text):
        return []
    rows: list[tuple[str, str, str, str, str, int | None]] = []
    for line, header in _rows(page.text, decimal_comma):
        metric = metric_of(line)
        label = _label(line)
        if metric is None or label is None:
            continue
        values = _values(line, decimal_comma)
        if not values or _is_prose(line, values):
            continue
        head = line[: label.end() + values[0].start]
        if _NOT_A_TOTAL.search(head) or _INTENSITY_AFTER.search(line[len(head) :]):
            continue
        row_unit = _ROW_UNIT.search(line, label.end())
        if row_unit:
            key, raw_unit = _unit_key(row_unit), row_unit.group(0)
        elif fallback:
            key, raw_unit = fallback
        else:
            continue
        column = header.index(report_year) if header and report_year in header else None
        if column is not None and column < len(values):
            token, year = values[column], report_year
        else:
            token, year = values[0], None
        if token.is_number:
            rows.append((metric, token.text, key, raw_unit, line[:200], year))
    out = []
    for metric, figure, key, raw_unit, quote, year in rows:
        try:
            value: Decimal | None = to_tonnes(parse_number(figure, decimal_comma), key)
        except UnitError:
            value = None
        out.append(
            ReportedMetric(
                page.doc_id,
                metric,
                float(value) if value is not None else None,
                page.number,
                raw_unit,
                quote,
                len(rows),
                column_year=year,
            )
        )
    return out


def extract(
    pages: Iterable[Page], decimal_comma: bool, report_year: int | None = None
) -> Iterator[ReportedMetric]:
    """All candidates, with at most one `selected` per metric (see the module docstring)."""
    candidates = [m for page in pages for m in extract_page(page, decimal_comma, report_year)]

    def rank(m: ReportedMetric) -> tuple[bool, int, bool, float]:
        return (
            m.column_year is not None,
            m.rows_on_page,
            bool(_GROUP_TOTAL.search(m.quote[:80])),
            m.value_t or 0.0,
        )

    best: dict[str, ReportedMetric] = {}
    for m in candidates:
        if m.value_t is None or m.rows_on_page < MIN_TABLE_ROWS:
            continue
        current = best.get(m.metric)
        if current is None or rank(m) > rank(current):
            best[m.metric] = m
    chosen = {id(m) for m in best.values()}
    for m in candidates:
        yield replace(m, selected=id(m) in chosen)
