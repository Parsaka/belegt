# ADR 0003: Answers only with page citations, tenant filter before retrieval

## Context
Answers about a company's emissions are only useful if a reader can check them. An answer
that is fluent but unsupported is worse than no answer.

## Decision
- Chunks never cross a page, so every citation names one page.
- The tenant filter runs before retrieval: in BigQuery the `VECTOR_SEARCH` base table is
  filtered on `tenant_id`, and row access policies enforce the same rule for each service
  identity. The tenant comes from the bearer token, never from the request body.
- After generation, every sentence must cite at least one retrieved chunk id. If a sentence has
  no citation, or cites a chunk that was not retrieved, the system abstains with a fixed sentence.
- Text inside sources is data. The prompt says so, and the citation check catches a model that
  follows a planted instruction anyway (`tests/test_rag.py`).
- A model-free extractive answerer runs offline, in CI and when the LLM spend cap is hit.

## Consequences
Some correct but uncited answers are rejected. That is the intended trade-off.
