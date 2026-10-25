"""Match free-text parent company names (EEA) to GLEIF legal entities.

Names are normalised (case, umlauts, legal-form suffixes, punctuation), then scored by token
overlap. A city match adds evidence. Exact normalised matches are accepted; weaker matches go to
a review queue; a human decision in `dbt/seeds/entity_overrides.csv` always wins.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass

from belegt.loaders.gleif import LegalEntity

LEGAL_FORMS = {
    "ag", "se", "gmbh", "mbh", "kg", "kgaa", "ohg", "ug", "co", "eg", "ev", "aktiengesellschaft",
    "gesellschaft", "beschrankter", "beschraenkter", "haftung", "und", "sa", "nv", "bv",
    "ltd", "plc", "inc", "holding",
}  # fmt: skip
ACCEPT = 0.95
REVIEW = 0.6
REGISTER_REVIEW = 0.2  # name overlap needed before a shared register number means anything


def normalise(name: str) -> str:
    text = name.lower().replace("ß", "ss")
    text = text.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(t for t in text.split() if t not in LEGAL_FORMS)


def score(a: str, b: str) -> float:
    ta, tb = set(normalise(a).split()), set(normalise(b).split())
    if not ta or not tb:
        return 0.0
    if ta == tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)


@dataclass(frozen=True)
class Match:
    source_name: str
    lei: str | None
    legal_name: str | None
    score: float
    decision: str  # accepted | review | unmatched
    evidence: str


def resolve(name: str, city: str | None, candidates: Iterable[LegalEntity]) -> Match:
    best: tuple[float, LegalEntity] | None = None
    for entity in candidates:
        s = score(name, entity.legal_name)
        if city and entity.city and normalise(city) == normalise(entity.city):
            s = min(1.0, s + 0.1)
        if entity.entity_status != "ACTIVE":
            s *= 0.9
        if best is None or s > best[0]:
            best = (s, entity)
    if best is None or best[0] < REVIEW:
        return Match(
            name, None, None, round(best[0], 3) if best else 0.0, "unmatched", "no candidate"
        )
    s, entity = best
    decision = "accepted" if s >= ACCEPT else "review"
    evidence = f"tokens {normalise(name)!r} vs {normalise(entity.legal_name)!r}"
    if city and entity.city and normalise(city) == normalise(entity.city):
        evidence += f", same city {entity.city}"
    return Match(name, entity.lei, entity.legal_name, round(s, 3), decision, evidence)


def normalise_lei(text: object) -> str | None:
    """The registry writes LEIs with dashes (5299-00RVRNBYTWP2VG-82); GLEIF has 20 characters."""
    if not text:
        return None
    lei = re.sub(r"[^A-Za-z0-9]", "", str(text)).upper()
    return lei if len(lei) == 20 else None


def normalise_register(text: object) -> str | None:
    """'HRB 6000', 'HRB6000 ' and 'hrb 6000' are the same Handelsregister number."""
    if not text:
        return None
    m = re.search(r"\b(HRA|HRB|GnR|PR|VR|FN)\s*\.?-?\s*(\d+)\s*([A-Za-z]?)\b", str(text), re.I)
    return f"{m[1].upper()} {m[2]}{m[3].upper()}" if m else None


def resolve_operator(
    name: str,
    registry_lei: str | None,
    register_nr: str | None,
    city: str | None,
    entities: list[LegalEntity],
    by_lei: dict[str, LegalEntity] | None = None,
) -> Match:
    """Strongest evidence first: the LEI the operator gave the registry, then the register number
    (only together with a plausible name, since numbers repeat across courts), then the name."""
    by_lei = by_lei if by_lei is not None else {e.lei: e for e in entities}
    lei = normalise_lei(registry_lei)
    if lei and lei in by_lei:
        e = by_lei[lei]
        return Match(name, lei, e.legal_name, 1.0, "accepted", "LEI reported in the Union Registry")
    reg = normalise_register(register_nr)
    if reg:
        same = sorted(
            (e for e in entities if normalise_register(e.registered_as) == reg),
            key=lambda e: -score(name, e.legal_name),
        )
        if same:
            e = same[0]
            s = score(name, e.legal_name)
            if s >= 0.5:
                return Match(name, e.lei, e.legal_name, 1.0, "accepted",
                             f"register number {reg} and name similarity {s:.2f}")  # fmt: skip
            if s >= REGISTER_REVIEW:  # e.g. a renamed company
                return Match(name, e.lei, e.legal_name, round(s, 3), "review",
                             f"register number {reg}, names differ ({s:.2f})")  # fmt: skip
            # same number, unrelated name: another court's register, so ignore it
    return resolve(name, city, entities)


class CandidateIndex:
    """Blocking: only entities that share a name token or the register number are compared.

    Without it every name would be scored against all 3.4 million GLEIF records.
    """

    def __init__(self, entities: Iterable[LegalEntity]) -> None:
        self.entities = list(entities)
        self._by_token: dict[str, list[LegalEntity]] = {}
        self._by_register: dict[str, list[LegalEntity]] = {}
        for e in self.entities:
            for token in set(normalise(e.legal_name).split()):
                self._by_token.setdefault(token, []).append(e)
            if reg := normalise_register(e.registered_as):
                self._by_register.setdefault(reg, []).append(e)

    def candidates(self, name: str, register_nr: object = None) -> list[LegalEntity]:
        found: dict[str, LegalEntity] = {}
        for token in set(normalise(name).split()):
            for e in self._by_token.get(token, []):
                found[e.lei] = e
        if reg := normalise_register(register_nr):
            for e in self._by_register.get(reg, []):
                found[e.lei] = e
        return list(found.values())
