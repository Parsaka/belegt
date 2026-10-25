"""Normalise emission quantities to tonnes CO2e.

Reports mix units (t, kt, Mt) and number formats ("1.234,5" in German, "1,234.5" in English).
Unit errors are the most common bug in this data, so every extracted figure goes through here.
"""

from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

UNIT_FACTORS: dict[str, Decimal] = {
    "t": Decimal(1),
    "kt": Decimal(1_000),
    "mt": Decimal(1_000_000),
}

_UNIT_ALIASES: dict[str, str] = {
    "t": "t",
    "tonnes": "t",
    "tons": "t",
    "tonnen": "t",
    "kt": "kt",
    "tsd. t": "kt",
    "thousand t": "kt",
    "mt": "mt",
    "mio. t": "mt",
    "million t": "mt",
}

_QUANTITY = re.compile(
    r"^\s*(?P<number>[+-]?[\d.,\s]+?)\s*(?P<unit>[a-zA-Z][a-zA-Z.\s]*?)?\s*(co2e?|co₂e?)?\s*$",
    re.IGNORECASE,
)


class UnitError(ValueError):
    pass


def parse_number(text: str, decimal_comma: bool) -> Decimal:
    """Parse a number written with either decimal convention."""
    cleaned = text.replace(" ", "").replace("\u202f", "")
    if decimal_comma:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", "")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise UnitError(f"not a number: {text!r}") from exc


def to_tonnes(value: Decimal, unit: str) -> Decimal:
    key = _UNIT_ALIASES.get(unit.strip().lower())
    if key is None:
        raise UnitError(f"unknown unit: {unit!r}")
    return value * UNIT_FACTORS[key]


def parse_quantity(text: str, decimal_comma: bool, default_unit: str | None = None) -> Decimal:
    """Parse a string such as "1.234,5 kt CO2e" into tonnes CO2e.

    `decimal_comma` must come from the document's language, never be guessed per number:
    "1.234" is 1234 in German and 1.234 in English.
    """
    match = _QUANTITY.match(text)
    if match is None:
        raise UnitError(f"not a quantity: {text!r}")
    unit = (match.group("unit") or "").strip() or default_unit
    if unit is None:
        raise UnitError(f"no unit in {text!r} and no default given")
    return to_tonnes(parse_number(match.group("number"), decimal_comma), unit)
