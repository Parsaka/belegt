from pathlib import Path

import pytest

from belegt.sources import SOURCES, Verification, get

DOC = Path(__file__).resolve().parents[1] / "docs" / "data-sources.md"


def test_ids_are_unique():
    ids = [s.id for s in SOURCES]
    assert len(ids) == len(set(ids))


def test_every_source_is_documented():
    text = DOC.read_text(encoding="utf-8")
    for source in SOURCES:
        assert f"`{source.id}`" in text, f"{source.id} missing from docs/data-sources.md"


def test_not_fully_verified_sources_name_their_open_question():
    for source in SOURCES:
        if source.verification is not Verification.VERIFIED:
            assert source.open_question


def test_get_unknown_raises():
    with pytest.raises(KeyError):
        get("nope")
