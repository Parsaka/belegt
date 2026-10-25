from __future__ import annotations

import hashlib
import math
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
