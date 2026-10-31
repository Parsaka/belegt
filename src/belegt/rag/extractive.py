"""A model-free LanguageModel: quotes the best-matching sentence with its chunk id.

It keeps the API usable offline and in CI, and is the fallback when the LLM spend cap is hit.
It reads the prompt the same way a real model would, so it goes through the same citation check.

A sentence is a prose sentence or a table row (one line of the page). A row such as "Gross
Scope 1 GHG emissions 1.25 0.93 1.014" does not name its company or year; the source does, in
its title and document id ("Covestro AG, report 2024", "covestro-2024"), so those words count
as part of every sentence in it.

Names are identifiers. The model knows the companies of the report list (`entities`); a
question that names one is answered only from a source about it, never from a similar row of
another company's report, however many other words match.
"""

from __future__ import annotations

import re
from collections.abc import Iterable

from belegt.documents.chunking import doc_of
from belegt.rag.answer import ABSTAIN_DE
from belegt.rag.embedding import STOPWORDS
from belegt.rag.names import entity_words, question_words, report_entities, strip_possessive

__all__ = ["ExtractiveModel", "entity_words", "report_entities"]

_SOURCE = re.compile(
    r"^\[(?P<id>[^\]]+)\] \(S\. \d+\)(?: (?P<title>[^\n]*))?\n(?P<text>.*?)(?=\n\n\[|\n\nFrage:)",
    re.S | re.M,
)
_QUESTION = re.compile(r"\nFrage: (?P<q>.*)\nAntwort:", re.S)
# a single letter or digit that stands alone: "Scope 1", "Mandant B", not the 1 of "1,887"
_SINGLE = r"(?<![\d.,])\b[A-Z0-9]\b(?![.,]\d)"
# words of three letters or more, plus single letters and digits ("Mandant B", "Scope 1")
_WORD = re.compile(rf"\w{{3,}}|{_SINGLE}")
_QUESTION_WORDS = frozenset(
    [
        *("hoch", "viel", "viele", "welche", "welcher", "welches", "wann", "warum", "betrug"),
        *("betrugen", "what", "were", "was", "how", "much", "many", "which", "did", "its"),
        *("jahr", "year", "waren"),
    ]
)
# a prose sentence ends with punctuation before a capital; a table row ends with its line
_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ])|\n")
MIN_COVERAGE = 0.75  # share of the question's words the quoted sentence must contain
# Single-letter and single-digit tokens name things ("Mandant B", "Scope 1"). A sentence about
# Mandant A must never answer a question about Mandant B, however many other words match.
_IDENTIFIER = re.compile(_SINGLE)


# footnote marks glued to a word or figure ("Scope 1²") are not part of it
_SUPERSCRIPTS = str.maketrans(dict.fromkeys("⁰¹²³⁴⁵⁶⁷⁸⁹", " "))
# a figure: a decimal or a number of two digits or more that is not a year
_FIGURE = re.compile(r"\d+[.,]\d+|\b(?!(?:19|20)\d\d\b)\d{2,}\b")


def _words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text.translate(_SUPERSCRIPTS))} - STOPWORDS


def _matched(wanted: set[str], words: set[str]) -> set[str]:
    """The wanted words a sentence contains, also as the end of a German compound:
    "Emissionen" is in "Scope-1-THG-Bruttoemissionen"."""
    return {w for w in wanted if w in words or (len(w) >= 5 and any(x.endswith(w) for x in words))}


class ExtractiveModel:
    def __init__(self, entities: Iterable[str] = ()) -> None:
        self._entities = frozenset(w.lower() for w in entities)

    def complete(self, prompt: str) -> str:
        question = _QUESTION.search(prompt)
        if question is None:
            return ABSTAIN_DE
        q = strip_possessive(question.group("q"))
        wanted = _words(q) - _QUESTION_WORDS
        if not wanted:
            return ABSTAIN_DE
        asked = question_words(q)
        identifiers = {w.lower() for w in _IDENTIFIER.findall(q)}
        identifiers |= asked & self._entities
        # (words matched, -names the source has that the question lacks, states a figure,
        # -other words), sentence, chunk id: asked about "Siemens", a Siemens AG source beats a
        # Siemens Energy one; a table row with its figures beats the table's heading and prose
        best: tuple[tuple[int, int, bool, int], str, str] | None = None
        for match in _SOURCE.finditer(prompt):
            title = match.group("title") or ""
            source = {w.lower() for w in re.findall(r"\w+", f"{title} {doc_of(match.group('id'))}")}
            extra = len((source & self._entities) - asked)
            for sentence in _SPLIT.split(match.group("text").strip()):
                if not sentence.strip():
                    continue
                words = _words(sentence) | source
                if not identifiers <= words:
                    continue
                matched = _matched(wanted, words)
                # other words: a table row says little besides its label and figures
                noise = sum(1 for w in words - matched - source if not w.isdigit())
                score = (len(matched), -extra, bool(_FIGURE.search(sentence)), -noise)
                if score[0] and (best is None or score > best[0]):
                    best = (score, sentence.rstrip(".!? "), match.group("id"))
        if best is None or best[0][0] / len(wanted) < MIN_COVERAGE:
            return ABSTAIN_DE
        return f"{best[1]} [{best[2]}]."
