from pathlib import Path

from belegt.rag.embedding import CachingEmbedder, HashingEmbedder


class CountingEmbedder:
    def __init__(self) -> None:
        self.inner = HashingEmbedder()
        self.dim = self.inner.dim
        self.calls: list[tuple[list[str], bool]] = []

    def embed(self, texts: list[str], *, query: bool) -> list[list[float]]:
        self.calls.append((list(texts), query))
        return self.inner.embed(texts, query=query)


def test_passages_are_embedded_once_and_reused_from_the_file(tmp_path: Path) -> None:
    path = tmp_path / "vectors.jsonl"
    first = CountingEmbedder()
    texts = ["Gross Scope 1 emissions 15.552", "Scope 2 market-based 2.396"]
    vectors = CachingEmbedder(first, path, "hashing").embed(texts, query=False)
    assert vectors == HashingEmbedder().embed(texts, query=False)
    assert len(first.calls) == 1

    # A second process (the next pipeline step) reads the file and embeds only new text.
    second = CountingEmbedder()
    again = CachingEmbedder(second, path, "hashing")
    assert again.embed(texts, query=False) == vectors
    assert second.calls == []
    again.embed([*texts, "Total gross Scope 3 emissions 91.64"], query=False)
    assert second.calls == [(["Total gross Scope 3 emissions 91.64"], False)]


def test_queries_are_never_cached(tmp_path: Path) -> None:
    inner = CountingEmbedder()
    cached = CachingEmbedder(inner, tmp_path / "vectors.jsonl", "hashing")
    cached.embed(["Scope 1?"], query=True)
    cached.embed(["Scope 1?"], query=True)
    assert len(inner.calls) == 2
    assert not (tmp_path / "vectors.jsonl").exists()


def test_the_model_name_is_part_of_the_key(tmp_path: Path) -> None:
    path = tmp_path / "vectors.jsonl"
    CachingEmbedder(CountingEmbedder(), path, "hashing").embed(["text"], query=False)
    other = CountingEmbedder()
    CachingEmbedder(other, path, "e5").embed(["text"], query=False)
    assert len(other.calls) == 1


def test_duplicate_passages_in_one_batch_are_embedded_once(tmp_path: Path) -> None:
    inner = CountingEmbedder()
    out = CachingEmbedder(inner, tmp_path / "v.jsonl", "hashing").embed(["a b", "a b"], query=False)
    assert inner.calls == [(["a b"], False)]
    assert out[0] == out[1]
