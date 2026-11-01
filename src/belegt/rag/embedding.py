from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Protocol

# Function words carry no topic; without this the hashing embedder matches on "der" and "die".
STOPWORDS = frozenset(
    [
        "der",
        "die",
        "das",
        "und",
        "oder",
        "in",
        "im",
        "am",
        "an",
        "auf",
        "aus",
        "bei",
        "mit",
        "von",
        "zu",
        "zum",
        "zur",
        "für",
        "ist",
        "sind",
        "war",
        "waren",
        "wie",
        "wer",
        "was",
        "wo",
        "hat",
        "haben",
        "ein",
        "eine",
        "einer",
        "eines",
        "den",
        "dem",
        "des",
        "nicht",
        "als",
        "auch",
        "the",
        "of",
        "and",
    ]
)


class Embedder(Protocol):
    dim: int

    def embed(self, texts: list[str], *, query: bool) -> list[list[float]]: ...


class HashingEmbedder:
    """Deterministic bag-of-words embedder for tests and offline runs. Not semantic."""

    def __init__(self, dim: int = 256) -> None:
        self.dim = dim

    def embed(self, texts: list[str], *, query: bool) -> list[list[float]]:
        out = []
        for text in texts:
            vec = [0.0] * self.dim
            for token in text.lower().split():
                token = token.strip(".,;:()[]\"'")
                if not token or token in STOPWORDS:
                    continue
                h = int(hashlib.md5(token.encode()).hexdigest(), 16)
                vec[h % self.dim] += 1.0
            norm = math.sqrt(sum(v * v for v in vec)) or 1.0
            out.append([v / norm for v in vec])
        return out


class E5Embedder:
    """multilingual-e5-small (MIT, 384 dimensions). Requires the `embed` extra."""

    dim = 384

    def __init__(self, model: str = "intfloat/multilingual-e5-small") -> None:
        from sentence_transformers import SentenceTransformer

        self._model = SentenceTransformer(model)

    def embed(self, texts: list[str], *, query: bool) -> list[list[float]]:
        prefix = "query: " if query else "passage: "  # e5 is trained with these prefixes
        vectors = self._model.encode([prefix + t for t in texts], normalize_embeddings=True)
        return [list(map(float, v)) for v in vectors]


class CachingEmbedder:
    """Wraps an embedder and keeps passage vectors in a JSON-lines file.

    The pipeline embeds the same chunks for the offline eval, the BigQuery load and the
    BigQuery eval; on a CPU runner each pass over the report corpus takes minutes. The key is
    the model name and the passage text, so a changed chunk or model is embedded again. Query
    vectors are never cached: questions are few and change with the cases.
    """

    def __init__(self, inner: Embedder, path: Path, model: str) -> None:
        self._inner = inner
        self._path = path
        self._model = model
        self.dim = inner.dim
        self._vectors: dict[str, list[float]] = {}
        if path.exists():
            for line in path.read_text().splitlines():
                if line.strip():
                    row = json.loads(line)
                    self._vectors[row["key"]] = row["vector"]

    def _key(self, text: str) -> str:
        return hashlib.sha256(f"{self._model}\n{text}".encode()).hexdigest()

    def embed(self, texts: list[str], *, query: bool) -> list[list[float]]:
        if query:
            return self._inner.embed(texts, query=True)
        keys = [self._key(t) for t in texts]
        missing = sorted(
            {k: t for k, t in zip(keys, texts, strict=True) if k not in self._vectors}.items()
        )
        if missing:
            vectors = self._inner.embed([t for _, t in missing], query=False)
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with self._path.open("a") as f:
                for (key, _), vec in zip(missing, vectors, strict=True):
                    self._vectors[key] = vec
                    f.write(json.dumps({"key": key, "vector": vec}) + "\n")
        return [self._vectors[k] for k in keys]
