"""Split pages into chunks that never cross a page boundary.

A chunk must belong to exactly one page, or a citation like "S. 187" would be wrong. Lines stay
whole: a table row ("Gross Scope 1 GHG emissions 1.25 0.93 1.014") is one line of the page, and
a chunk that cut it would separate the row's label from its figures.
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


def _pieces(paragraph: str, max_chars: int) -> list[str]:
    """Whole lines packed into pieces of at most `max_chars`; only an overlong line is cut."""
    out: list[str] = []
    current = ""
    for line in paragraph.split("\n"):
        while len(line) > max_chars:
            if current:
                out.append(current)
                current = ""
            out.append(line[:max_chars])
            line = line[max_chars:]
        if current and len(current) + 1 + len(line) > max_chars:
            out.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        out.append(current)
    return out


def _tail(text: str, size: int) -> str:
    """The last whole lines of `text`, at most `size` characters: the overlap."""
    kept: list[str] = []
    for line in reversed(text.split("\n")):
        if sum(len(k) + 1 for k in kept) + len(line) > size:
            break
        kept.insert(0, line)
    return "\n".join(kept)


def chunk_id(doc_id: str, page: int, index: int) -> str:
    digest = hashlib.sha1(f"{doc_id}|{page}|{index}".encode()).hexdigest()[:16]
    return f"{doc_id}:{page}:{digest}"


def doc_of(chunk_id: str) -> str:
    return chunk_id.split(":", 1)[0]


def page_of(chunk_id: str) -> int | None:
    parts = chunk_id.split(":")
    return int(parts[1]) if len(parts) == 3 and parts[1].isdigit() else None


def chunk_pages(
    pages: Iterable[Page],
    tenant_id: str,
    max_chars: int = 1200,
    overlap: int = 150,
    title: str | None = None,
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
            for piece in _pieces(para, max_chars - overlap):
                if buffer and len(buffer) + 1 + len(piece) > max_chars:
                    yield Chunk(
                        chunk_id(page.doc_id, page.number, index),
                        page.doc_id,
                        tenant_id,
                        page.number,
                        buffer,
                        heading,
                        title,
                    )
                    index += 1
                    tail = _tail(buffer, overlap) if overlap else ""
                    buffer = f"{tail}\n{piece}" if tail else piece
                else:
                    buffer = f"{buffer}\n{piece}" if buffer else piece
        if buffer:
            yield Chunk(
                chunk_id(page.doc_id, page.number, index),
                page.doc_id,
                tenant_id,
                page.number,
                buffer,
                heading,
                title,
            )
