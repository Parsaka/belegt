"""Evaluation of the document assistant: correct answers, correct abstentions, zero leaks.

A case names a tenant, a question and what must happen:

- `expect: answer` with the document (`doc`) that must be cited and, optionally, a phrase the
  answer must contain;
- `expect: abstain` when the answer is not in what this tenant may see. Questions about another
  tenant's documents are abstain cases: answering them is a leak.

The same cases run offline in CI (in-memory retriever) and in the cloud (BigQuery, as each
tenant's own identity, with row access policies), so the cloud numbers prove the policies.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path

from belegt.documents.model import SHARED_TENANT
from belegt.rag.answer import Answerer


@dataclass(frozen=True)
class Case:
    id: str
    tenant: str
    question: str
    expect: str  # "answer" or "abstain"
    doc: str | None = None
    contains: str | None = None


@dataclass(frozen=True)
class Outcome:
    case: Case
    passed: bool
    abstained: bool
    cited_docs: tuple[str, ...]
    leaked: bool
    note: str


def read_cases(path: Path) -> list[Case]:
    cases = [Case(**json.loads(line)) for line in path.read_text().splitlines() if line.strip()]
    for c in cases:
        if c.expect not in {"answer", "abstain"} or (c.expect == "answer" and not c.doc):
            raise ValueError(f"case {c.id}: answer cases need a doc, expect is answer|abstain")
    return cases


def doc_of(chunk_id: str) -> str:
    return chunk_id.split(":", 1)[0]


def judge(
    case: Case, text: str, abstained: bool, citations: list[str], owners: dict[str, str]
) -> Outcome:
    docs = tuple(dict.fromkeys(doc_of(c) for c in citations))
    leaked = any(owners.get(d, SHARED_TENANT) not in (case.tenant, SHARED_TENANT) for d in docs)
    if leaked:
        return Outcome(case, False, abstained, docs, True, "cited another tenant's document")
    if case.expect == "abstain":
        return Outcome(case, abstained, abstained, docs, False, "" if abstained else "answered")
    if abstained:
        return Outcome(case, False, True, docs, False, "abstained")
    if case.doc not in docs:
        return Outcome(case, False, False, docs, False, f"did not cite {case.doc}")
    if case.contains and case.contains.lower() not in text.lower():
        return Outcome(case, False, False, docs, False, f"answer lacks {case.contains!r}")
    return Outcome(case, True, False, docs, False, "")


def run(cases: Iterable[Case], answerer: Answerer, owners: dict[str, str]) -> list[Outcome]:
    """`owners` maps doc_id to tenant, to detect leaks independently of the retriever."""
    out = []
    for case in cases:
        result = answerer.ask(case.question, case.tenant)
        out.append(judge(case, result.text, result.abstained, result.citations, owners))
    return out


def report(outcomes: list[Outcome], title: str) -> str:
    answer = [o for o in outcomes if o.case.expect == "answer"]
    abstain = [o for o in outcomes if o.case.expect == "abstain"]
    leaks = sum(o.leaked for o in outcomes)

    def share(part: list[Outcome]) -> str:
        return f"{sum(o.passed for o in part)}/{len(part)}" if part else "n/a"

    lines = [
        f"# {title}",
        "",
        "| metric | result |",
        "|---|---|",
        f"| answered correctly (cites the right document) | {share(answer)} |",
        f"| abstained correctly | {share(abstain)} |",
        f"| **leaks** (cited another tenant's document) | **{leaks}** |",
        "",
        "| case | tenant | expect | passed | cited | note |",
        "|---|---|---|---|---|---|",
    ]
    lines += [
        f"| {o.case.id} | {o.case.tenant} | {o.case.expect} | {'yes' if o.passed else 'no'} "
        f"| {', '.join(o.cited_docs)} | {o.note} |"
        for o in outcomes
    ]
    return "\n".join(lines) + "\n"
