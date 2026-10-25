import pytest

from belegt.documents.chunking import chunk_pages
from belegt.documents.model import Page

PAGES = [
    Page(
        "acme-2024", 1, "E1-6 Treibhausgasemissionen\n\n" + "Scope 1 betrug 1,2 Mio. t CO2e. " * 60
    ),
    Page("acme-2024", 2, "Die Methodik folgt dem GHG Protocol."),
]


def test_chunks_never_cross_pages_and_respect_size():
    chunks = list(chunk_pages(PAGES, "shared", max_chars=400, overlap=50))
    assert {c.page for c in chunks} == {1, 2}
    assert all(len(c.text) <= 400 + 50 + 1 for c in chunks)
    assert chunks[-1].text == "Die Methodik folgt dem GHG Protocol."


def test_ids_are_deterministic_and_unique():
    a = [c.chunk_id for c in chunk_pages(PAGES, "shared", max_chars=400, overlap=50)]
    b = [c.chunk_id for c in chunk_pages(PAGES, "shared", max_chars=400, overlap=50)]
    assert a == b
    assert len(set(a)) == len(a)


def test_heading_is_carried_to_following_chunks():
    chunks = list(chunk_pages(PAGES, "shared", max_chars=400, overlap=50))
    assert all(c.heading == "E1-6 Treibhausgasemissionen" for c in chunks)


def test_citation_names_the_page():
    chunk = next(iter(chunk_pages(PAGES[1:], "shared")))
    assert (
        chunk.citation("ACME Nachhaltigkeitserklärung 2024")
        == "ACME Nachhaltigkeitserklärung 2024, S. 2"
    )


def test_overlap_must_be_smaller_than_size():
    with pytest.raises(ValueError):
        list(chunk_pages(PAGES, "shared", max_chars=100, overlap=100))
