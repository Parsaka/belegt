"""Extract text page by page. Requires the `docs` extra (pypdf)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from belegt.documents.model import Page


def read_pages(path: Path, doc_id: str) -> Iterator[Page]:
    from pypdf import PdfReader

    reader = PdfReader(str(path))
    for number, page in enumerate(reader.pages, start=1):
        yield Page(doc_id=doc_id, number=number, text=page.extract_text() or "")
