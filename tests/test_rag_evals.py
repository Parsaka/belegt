"""The evaluation cases pass offline, and the judge counts leaks independently of retrieval."""

from pathlib import Path

from belegt.api.app import load_chunks
from belegt.rag.answer import Answerer
from belegt.rag.embedding import HashingEmbedder
from belegt.rag.evals import Case, judge, read_cases, report, run
from belegt.rag.extractive import ExtractiveModel
from belegt.rag.retrieval import InMemoryRetriever

ROOT = Path(__file__).parents[1]


def test_eval_cases_pass_on_the_demo_corpus(tmp_path):
    corpus = load_chunks(ROOT / "deploy" / "kind" / "demo-chunks.jsonl")
    owners = {c.doc_id: c.tenant_id for c in corpus}
    retriever = InMemoryRetriever(HashingEmbedder(), corpus)
    outcomes = run(
        read_cases(ROOT / "evals" / "rag_cases.jsonl"),
        Answerer(retriever, ExtractiveModel(), min_score=0.1),
        owners,
    )
    assert not [o for o in outcomes if o.leaked]
    assert all(o.passed for o in outcomes), report(outcomes, "failed")


def test_a_citation_of_another_tenants_document_is_a_leak_even_if_retrieval_allowed_it():
    case = Case("x", "tenant_a", "q", "abstain")
    owners = {"b-memo": "tenant_b", "esrs": "shared"}
    outcome = judge(case, "text [b-memo:1:abc]", False, ["b-memo:1:abc"], owners)
    assert outcome.leaked and not outcome.passed
    assert not judge(case, "t [esrs:1:a]", False, ["esrs:1:a"], owners).leaked
