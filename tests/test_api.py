import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from belegt.api.app import RateLimiter, create_app, parse_tokens
from belegt.documents.chunking import chunk_pages
from belegt.documents.model import Page
from belegt.rag.answer import Answerer
from belegt.rag.embedding import HashingEmbedder
from belegt.rag.extractive import ExtractiveModel
from belegt.rag.retrieval import InMemoryRetriever

PAGE = Page(
    "acme-2024", 12, "Die Scope-1-Emissionen der ACME AG betrugen 2024 insgesamt 1,2 Mio. t CO2e."
)


def client(limit=5):
    retriever = InMemoryRetriever(HashingEmbedder(), list(chunk_pages([PAGE], "shared")))
    app = create_app(
        Answerer(retriever, ExtractiveModel(), min_score=0.1),
        parse_tokens("demo:tenant_a"),
        RateLimiter(limit=limit, window_s=60),
    )
    return TestClient(app)


def test_health():
    assert client().get("/health").json() == {"status": "ok"}


def test_ask_requires_known_token():
    r = client().post(
        "/ask", json={"question": "Scope 1?"}, headers={"Authorization": "Bearer nope"}
    )
    assert r.status_code == 401


def test_ask_returns_cited_answer():
    r = client().post(
        "/ask",
        json={"question": "Wie hoch waren die Scope-1-Emissionen der ACME AG?"},
        headers={"Authorization": "Bearer demo"},
    )
    assert r.status_code == 200
    body = r.json()
    assert not body["abstained"]
    assert body["citations"][0].startswith("acme-2024:12:")


def test_rate_limit():
    c = client(limit=2)
    headers = {"Authorization": "Bearer demo"}
    codes = [
        c.post("/ask", json={"question": "Scope 1?"}, headers=headers).status_code for _ in range(3)
    ]
    assert codes == [200, 200, 429]


def test_rate_limiter_window_expires():
    now = [0.0]
    limiter = RateLimiter(limit=1, window_s=10, clock=lambda: now[0])
    assert limiter.allow("t") and not limiter.allow("t")
    now[0] = 11
    assert limiter.allow("t")
