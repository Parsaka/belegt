"""A model-free LanguageModel: quotes the best-matching sentence with its chunk id.

It keeps the API usable offline and in CI, and is the fallback when the LLM spend cap is hit.
It reads the prompt the same way a real model would, so it goes through the same citation check.
"""

from __future__ import annotations

import re

from belegt.rag.answer import ABSTAIN_DE
from belegt.rag.embedding import STOPWORDS

_SOURCE = re.compile(
    r"^\[(?P<id>[^\]]+)\] \(S\. \d+\)\n(?P<text>.*?)(?=\n\n\[|\n\nFrage:)", re.S | re.M
)
_QUESTION = re.compile(r"\nFrage: (?P<q>.*)\nAntwort:", re.S)
# words of three letters or more, plus single letters and digits ("Mandant B", "Scope 1")
_WORD = re.compile(r"\w{3,}|\b[A-Z0-9]\b")
_QUESTION_WORDS = frozenset(
    ["hoch", "viel", "viele", "welche", "welcher", "welches", "wann", "warum", "betrug", "betrugen"]
)
MIN_COVERAGE = 0.75  # share of the question's words the quoted sentence must contain


def _words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text)} - STOPWORDS


class ExtractiveModel:
    def complete(self, prompt: str) -> str:
        question = _QUESTION.search(prompt)
        if question is None:
            return ABSTAIN_DE
        wanted = _words(question.group("q")) - _QUESTION_WORDS
        if not wanted:
            return ABSTAIN_DE
        best: tuple[int, str, str] | None = None
        for match in _SOURCE.finditer(prompt):
            for sentence in re.split(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])", match.group("text").strip()):
                overlap = len(wanted & _words(sentence))
                if overlap and (best is None or overlap > best[0]):
                    best = (overlap, sentence.rstrip(".!? "), match.group("id"))
        if best is None or best[0] / len(wanted) < MIN_COVERAGE:
            return ABSTAIN_DE
        return f"{best[1]} [{best[2]}]."
