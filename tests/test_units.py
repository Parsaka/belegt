from decimal import Decimal

import pytest

from belegt.units import UnitError, parse_number, parse_quantity, to_tonnes


@pytest.mark.parametrize(
    ("text", "decimal_comma", "expected"),
    [
        ("1.234,5", True, Decimal("1234.5")),
        ("1,234.5", False, Decimal("1234.5")),
        ("1.234", True, Decimal("1234")),
        ("1.234", False, Decimal("1.234")),
        ("12 345", True, Decimal("12345")),
        ("12\u202f345", True, Decimal("12345")),
    ],
)
def test_parse_number_respects_document_convention(text, decimal_comma, expected):
    assert parse_number(text, decimal_comma) == expected


@pytest.mark.parametrize(
    ("text", "decimal_comma", "expected"),
    [
        ("1.234,5 kt CO2e", True, Decimal("1234500")),
        ("12.3 Mt CO₂e", False, Decimal("12300000")),
        ("850 t", False, Decimal("850")),
        ("2,5 Mio. t CO2", True, Decimal("2500000")),
        ("3 Tsd. t", True, Decimal("3000")),
    ],
)
def test_parse_quantity_to_tonnes(text, decimal_comma, expected):
    assert parse_quantity(text, decimal_comma) == expected


def test_default_unit_used_when_table_header_gives_it():
    assert parse_quantity("4,2", decimal_comma=True, default_unit="Mt") == Decimal("4200000")


def test_missing_unit_without_default_is_an_error():
    with pytest.raises(UnitError):
        parse_quantity("4,2", decimal_comma=True)


def test_unknown_unit_is_an_error():
    with pytest.raises(UnitError):
        to_tonnes(Decimal(1), "gigatonnes of joy")
