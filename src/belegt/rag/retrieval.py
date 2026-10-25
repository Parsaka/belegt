"""Retrieval with the tenant filter applied before anything reaches the model.

Isolation has two layers: BigQuery row access policies restrict what each tenant's service
identity can read, and every query also filters on tenant explicitly. The in-memory retriever
mirrors the second layer so the isolation tests run offline.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from belegt.documents.model import SHARED_TENANT, Chunk
from belegt.rag.embedding import Embedder


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float  # cosine similarity, higher is closer


class Retriever(Protocol):
    def search(self, question: str, tenant_id: str, k: int) -> list[Hit]: ...


def visible_tenants(tenant_id: str) -> tuple[str, ...]:
    if not tenant_id or tenant_id == SHARED_TENANT:
        raise ValueError("a request must name a real tenant")
    return (tenant_id, SHARED_TENANT)


class InMemoryRetriever:
    def __init__(self, embedder: Embedder, chunks: list[Chunk]) -> None:
        self._embedder = embedder
        self._chunks = chunks
        self._vectors = embedder.embed([c.text for c in chunks], query=False)

    def search(self, question: str, tenant_id: str, k: int) -> list[Hit]:
        allowed = visible_tenants(tenant_id)
        (q,) = self._embedder.embed([question], query=True)
        hits = [
            Hit(chunk, sum(a * b for a, b in zip(q, vec, strict=True)))
            for chunk, vec in zip(self._chunks, self._vectors, strict=True)
            if chunk.tenant_id in allowed
        ]
        return sorted(hits, key=lambda h: h.score, reverse=True)[:k]


def bigquery_search_sql(dataset: str, k: int) -> str:
    """VECTOR_SEARCH over the chunks a tenant may see. Parameters: @tenant, @embedding.

    The base table is filtered before the search, so other tenants' rows are never candidates.
    Distance is cosine distance; score = 1 - distance.
    """
    return f"""
SELECT base.chunk_id, base.doc_id, base.tenant_id, base.page, base.heading, base.text,
       1 - distance AS score
FROM VECTOR_SEARCH(
  (SELECT * FROM `{dataset}.chunks` WHERE tenant_id IN (@tenant, '{SHARED_TENANT}')),
  'embedding',
  (SELECT @embedding AS embedding),
  top_k => {int(k)},
  distance_type => 'COSINE'
)
ORDER BY score DESC
""".strip()
