"""Company names as identifiers: which reports a question is about.

A report's GHG table looks like every other report's ("Gross Scope 1 GHG emissions 1.25 0.93
1.014"); only the company name tells them apart, and an embedding weighs that one word like any
other. So names are resolved before retrieval: a question that names a company of the report
list searches only that company's reports (a metadata filter, applied together with the tenant
filter), and the extractive model never quotes a source about another company.
"""

from __future__ import annotations

import csv
import re
from collections.abc import Iterable
from pathlib import Path

# legal forms and other words of company names that name nothing by themselves
_NOT_A_NAME = frozenset(
    ["ag", "se", "kgaa", "co", "gmbh", "aktiengesellschaft", "group", "holding", "report"]
)


_POSSESSIVE = re.compile(r"['\u2019]s\b")


def strip_possessive(text: str) -> str:
    """ "BASF's emissions" -> "BASF emissions": not BASF and S (as in K+S)."""
    return _POSSESSIVE.sub("", text)


def question_words(question: str) -> set[str]:
    """All words of a question, lower case."""
    return {w.lower() for w in re.findall(r"\w+", strip_possessive(question))}


def entity_words(names: Iterable[str]) -> frozenset[str]:
    """The words that identify a company: "Covestro AG" -> covestro, "K+S" -> k, s."""
    return (
        frozenset(w.lower() for name in names for w in re.findall(r"\w+", name) if not w.isdigit())
        - _NOT_A_NAME
    )


class ReportNames:
    """The companies of the report list, by document id."""

    def __init__(self, reports: Iterable[tuple[str, str]] = ()) -> None:
        self._words = {doc_id: entity_words([company, doc_id]) for doc_id, company in reports}

    @classmethod
    def from_seed(cls, seed: Path) -> ReportNames:
        if not seed.exists():
            return cls()
        with seed.open(newline="", encoding="utf-8") as fh:
            return cls((r["doc_id"], r["company"]) for r in csv.DictReader(fh))

    @property
    def words(self) -> frozenset[str]:
        return frozenset().union(*self._words.values())

    def named(self, question: str) -> frozenset[str] | None:
        """The reports of the company the question names best; None if it names none.

        "Siemens" names both Siemens and Siemens Energy (the model prefers the exact name);
        "Siemens Energy" names only Siemens Energy.
        """
        asked = question_words(question)
        overlap = {doc: len(words & asked) for doc, words in self._words.items()}
        best = max(overlap.values(), default=0)
        if not best:
            return None
        return frozenset(doc for doc, n in overlap.items() if n == best)


def report_entities(seed: Path) -> frozenset[str]:
    """Entity words of the report list: company names and document ids ("bmw-2024")."""
    return ReportNames.from_seed(seed).words
