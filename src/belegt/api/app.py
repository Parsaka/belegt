"""HTTP API: /health and /ask. Requires the `api` extra.

Each bearer token maps to exactly one tenant; the tenant never comes from the request body.
A fixed-window limit per token keeps a public demo from running up model costs.
"""

from __future__ import annotations

import json
import os
import time
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from belegt.documents.model import Chunk
from belegt.rag.answer import Answerer
from belegt.rag.embedding import HashingEmbedder
from belegt.rag.extractive import ExtractiveModel
from belegt.rag.retrieval import InMemoryRetriever, Retriever


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class AskResponse(BaseModel):
    answer: str
    abstained: bool
    citations: list[str]


class RateLimiter:
    def __init__(self, limit: int, window_s: float, clock: Callable[[], float] = time.monotonic):
        self.limit, self.window_s, self._clock = limit, window_s, clock
        self._hits: dict[str, list[float]] = defaultdict(list)

    def allow(self, key: str) -> bool:
        now = self._clock()
        recent = [t for t in self._hits[key] if now - t < self.window_s]
        self._hits[key] = recent
        if len(recent) >= self.limit:
            return False
        recent.append(now)
        return True


def load_chunks(path: Path) -> list[Chunk]:
    """Chunks as JSON lines, one Chunk per line (the output of `belegt index`)."""
    return [Chunk(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]


def parse_tokens(spec: str) -> dict[str, str]:
    """ "token1:tenant_a,token2:tenant_b" -> {token: tenant}."""
    pairs = (item.split(":", 1) for item in spec.split(",") if item.strip())
    return {token.strip(): tenant.strip() for token, tenant in pairs}


def create_app(
    answerer: Answerer, tokens: dict[str, str], limiter: RateLimiter | None = None
) -> FastAPI:
    app = FastAPI(title="Belegt", version="0.1.0")
    limiter = limiter or RateLimiter(limit=20, window_s=3600)

    def tenant(authorization: str = Header(default="")) -> str:
        token = authorization.removeprefix("Bearer ").strip()
        if token not in tokens:
            raise HTTPException(401, "unknown token")
        if not limiter.allow(token):
            raise HTTPException(429, "rate limit reached")
        return tokens[token]

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/ask", response_model=AskResponse)
    def ask(body: AskRequest, tenant_id: str = Depends(tenant)) -> AskResponse:
        result = answerer.ask(body.question, tenant_id)
        return AskResponse(
            answer=result.text, abstained=result.abstained, citations=result.citations
        )

    return app


def app_from_env() -> FastAPI:
    """Entry point for uvicorn --factory.

    BELEGT_BACKEND=memory (default): chunks from BELEGT_CHUNKS, for kind and local runs.
    BELEGT_BACKEND=bigquery: `rag.chunks` in BELEGT_PROJECT, each request as its tenant's
    identity, with the embedder the chunks were loaded with (BELEGT_EMBEDDER, default e5).
    BELEGT_TOKENS maps bearer tokens to tenants; in the cloud it comes from Secret Manager.
    """
    retriever: Retriever
    if os.environ.get("BELEGT_BACKEND", "memory") == "bigquery":
        from belegt.rag.bigquery import BigQueryRetriever, impersonating_client
        from belegt.rag.embedding import E5Embedder

        project = os.environ["BELEGT_PROJECT"]
        embedder = (
            E5Embedder() if os.environ.get("BELEGT_EMBEDDER", "e5") == "e5" else HashingEmbedder()
        )
        retriever = BigQueryRetriever(impersonating_client(project), f"{project}.rag", embedder)
    else:
        chunks = load_chunks(Path(os.environ.get("BELEGT_CHUNKS", "data/chunks.jsonl")))
        retriever = InMemoryRetriever(HashingEmbedder(), chunks)
    answerer = Answerer(retriever, ExtractiveModel(), min_score=0.1)
    return create_app(answerer, parse_tokens(os.environ.get("BELEGT_TOKENS", "")))
