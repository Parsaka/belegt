from __future__ import annotations

from dataclasses import dataclass

SHARED_TENANT = "shared"  # public corpus: sustainability statements and ESRS


@dataclass(frozen=True)
class Page:
    doc_id: str
    number: int  # 1-based, as printed in citations
    text: str


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    doc_id: str
    tenant_id: str
    page: int
    text: str
    heading: str | None = None
    title: str | None = None  # the document, e.g. "Covestro AG, annual report 2024"

    @property
    def passage(self) -> str:
        """What gets embedded: the document title and heading carry who and what the page is
        about, which a table page rarely says itself."""
        return "\n".join(part for part in (self.title, self.heading, self.text) if part)

    def citation(self, title: str | None = None) -> str:
        return f"{title or self.doc_id}, S. {self.page}"
