"""Split pages into chunks that never cross a page boundary.

A chunk must belong to exactly one page, or a citation like "S. 187" would be wrong.
"""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable, Iterator

from belegt.documents.model import Chunk, Page

_HEADING = re.compile(r"^(?:[A-Z]\d+(?:-\d+)?|\d+(?:\.\d+)*)\s+\S.{0,80}$")  # "E1-6 ...", "3.2 ..."


def _paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text.replace("\r\n", "\n"))
    return [re.sub(r"[ \t]+", " ", p).strip() for p in parts if p.strip()]


def chunk_id(doc_id: str, page: int, index: int) -> str:
    digest = hashlib.sha1(f"{doc_id}|{page}|{index}".encode()).hexdigest()[:16]
    return f"{doc_id}:{page}:{digest}"


def chunk_pages(
    pages: Iterable[Page], tenant_id: str, max_chars: int = 1200, overlap: int = 150
) -> Iterator[Chunk]:
    """Pack paragraphs into chunks of at most `max_chars`, carrying the last seen heading."""
    if overlap >= max_chars:
        raise ValueError("overlap must be smaller than max_chars")
    heading: str | None = None
    for page in pages:
        index = 0
        buffer = ""
        for para in _paragraphs(page.text):
            if _HEADING.match(para) and len(para) < 90:
                heading = para
            pieces = [para[i : i + max_chars] for i in range(0, len(para), max_chars - overlap)]
            for piece in pieces:
                if buffer and len(buffer) + 1 + len(piece) > max_chars:
                    yield Chunk(
                        chunk_id(page.doc_id, page.number, index),
                        page.doc_id,
                        tenant_id,
                        page.number,
                        buffer,
                        heading,
                    )
                    index += 1
                    buffer = buffer[-overlap:] + " " + piece if overlap else piece
                else:
                    buffer = f"{buffer} {piece}".strip()
        if buffer:
            yield Chunk(
                chunk_id(page.doc_id, page.number, index),
                page.doc_id,
                tenant_id,
                page.number,
                buffer,
                heading,
            )
