"""Greenhouse-gas totals from sustainability statements, each with the page it came from.

Reports put the ESRS E1-6 figures in a table: one row per scope, one column per year, and the
unit once in the table header ("in Mio. t CO2e"). The extractor works on that shape:

1. Find the unit on the page. Without a unit on the page, nothing on it is extracted.
2. Find the lines that start a scope row (Scope 1; Scope 2 market- or location-based;
   Scope 3 total). Lines that combine scopes ("Scope 1 und 2") are skipped.
3. Keep rows with at least two figures (reporting year and a comparison year), which drops
   prose such as "Scope 1 bis 2030 um 25 % senken". Take the first figure: tables list the
   reporting year first.

Every figure keeps the line it came from, so a person can check it against the page. The
selected figure per report and metric is the one from the page with the most scope rows (the
E1-6 table itself, not a narrative mention), and never from a page with a single scope row; the
others stay as candidates.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from decimal import Decimal

from belegt.documents.model import Page
from belegt.units import UnitError, parse_number, to_tonnes

METRICS = ("scope1", "scope2_market", "scope2_location", "scope3")
# A figure is selected only from a page with at least two scope rows: the E1-6 table lists
# Scope 1, 2 and 3 together, while a lone row is usually a target or an intensity in prose.
MIN_TABLE_ROWS = 2

_UNIT = re.compile(
    r"(?P<unit>Mio\.?\s*t|Millionen\s+(?:metrische\s+)?Tonnen|million\s+(?:metric\s+)?t(?:onnes|ons)?"
    r"|Tsd\.?\s*t|Tausend\s+(?:metrische\s+)?Tonnen|thousand\s+(?:metric\s+)?t(?:onnes|ons)?"
    r"|kt|t)\s*(?:CO2|CO₂)",
    re.IGNORECASE,
)
_UNIT_KEY = (
    (re.compile(r"^(mio|millionen|million)", re.I), "mt"),
    (re.compile(r"^(tsd|tausend|thousand|kt)", re.I), "kt"),
)
_SCOPE = re.compile(r"\bScope[\s-]*(?P<n>[123])\b(?!\s*(?:\+|und|and|&|/|,)\s*[123]\b)", re.I)
_MARKET = re.compile(r"marktbasiert|market[\s-]*based", re.I)
_LOCATION = re.compile(r"standortbasiert|location[\s-]*based", re.I)
_TOTAL = re.compile(r"gesamt|insgesamt|total", re.I)
# 12.345,6 or 12,3 (German); the comma/point roles are fixed per document language
_NUMBER_DE = re.compile(
    r"(?<![\w.,])\d{1,3}(?:\.\d{3})+(?:,\d+)?(?![\w.,])|(?<![\w.,])\d+(?:,\d+)?(?![\w.,])"
)
_NUMBER_EN = re.compile(
    r"(?<![\w.,])\d{1,3}(?:,\d{3})+(?:\.\d+)?(?![\w.,])|(?<![\w.,])\d+(?:\.\d+)?(?![\w.,])"
)
_YEAR = re.compile(r"^(?:19|20)\d{2}$")


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


def page_unit(text: str) -> tuple[str, str] | None:
    """(canonical unit, as written) for the first CO2 unit on the page."""
    match = _UNIT.search(text)
    if match is None:
        return None
    raw = match.group("unit")
    for pattern, key in _UNIT_KEY:
        if pattern.match(raw.strip()):
            return key, raw
    return "t", raw


def metric_of(line: str) -> str | None:
    match = _SCOPE.search(line)
    if match is None or match.start() > 40:  # the label starts the row, not the middle of prose
        return None
    n = match.group("n")
    if n == "1":
        return "scope1"
    if n == "2":
        if _MARKET.search(line):
            return "scope2_market"
        if _LOCATION.search(line):
            return "scope2_location"
        return None
    return "scope3" if _TOTAL.search(line) else None


def figures(line: str, decimal_comma: bool) -> list[str]:
    """Numbers after the scope label, without years and single-digit footnote markers."""
    label = _SCOPE.search(line)
    rest = line[label.end() :] if label else line
    pattern = _NUMBER_DE if decimal_comma else _NUMBER_EN
    return [
        m.group(0)
        for m in pattern.finditer(rest)
        if not _YEAR.match(m.group(0)) and not re.fullmatch(r"\d", m.group(0))
    ]


def first_figure(line: str, decimal_comma: bool) -> str | None:
    """The reporting-year figure of a table row: tables list it first."""
    found = figures(line, decimal_comma)
    return found[0] if found else None


def extract_page(page: Page, decimal_comma: bool) -> list[ReportedMetric]:
    unit = page_unit(page.text)
    if unit is None:
        return []
    key, raw_unit = unit
    rows: list[tuple[str, str, str]] = []
    for line in page.text.splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        metric = metric_of(line)
        if metric is None:
            continue
        found = figures(line, decimal_comma)
        if len(found) < 2:  # a table row has the reporting year and at least one comparison
            continue
        rows.append((metric, found[0], line[:200]))
    out = []
    for metric, figure, quote in rows:
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
            )
        )
    return out


def extract(pages: Iterable[Page], decimal_comma: bool) -> Iterator[ReportedMetric]:
    """All candidates, with exactly one `selected` per metric: the first one on the page with the
    most scope rows."""
    candidates = [m for page in pages for m in extract_page(page, decimal_comma)]
    best: dict[str, ReportedMetric] = {}
    for m in candidates:
        if m.value_t is None or m.rows_on_page < MIN_TABLE_ROWS:
            continue
        current = best.get(m.metric)
        if current is None or m.rows_on_page > current.rows_on_page:
            best[m.metric] = m
    chosen = {id(m) for m in best.values()}
    for m in candidates:
        yield ReportedMetric(**{**m.__dict__, "selected": id(m) in chosen})
