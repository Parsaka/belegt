# Document assistant on 37 real reports

This page asks one question: does the multi-tenant assistant answer from the real
sustainability reports, citing the right page, without leaking another tenant's reports?

## Result

Measured 2026-10-31 in Reports run
[41243480243](https://github.com/Parsaka/belegt/actions/runs/41243480243). The run used
multilingual-e5-small embeddings and in-memory retrieval with the same filters as BigQuery, over
4,915 chunks from the greenhouse-gas pages of 37 reports:

| | result |
|---|---|
| owner asks for the company's Scope 1 figure | **19 of 31** answered with the printed figure and a citation on a labelled page |
| the other tenant asks the same question | **31 of 31** declined |
| cross-tenant leaks (a citation of a report the tenant may not read) | **0** |

The report with every case is `runs/reports/<run>/summary-discover/rag-eval-reports-runner.md`
on the `ops-results` branch. After a merge to `main`, the Pipeline workflow runs the same cases
on BigQuery `VECTOR_SEARCH`, with each question run under the tenant's own service account
(`rag-eval-reports-bigquery.md`).

## Method

- **Corpus.** Each report is owned by one tenant (`evals/rag_corpus.csv`): energy and materials
  belong to `tenant_a`, and mobility, logistics and technology belong to `tenant_b`.
  `belegt index-reports` chunks only the pages that mention a scope, GHG/THG or E1-6. Each chunk
  never crosses a page, keeps table rows whole, and is titled "{company}, report {year}".
- **Cases.** The cases are built from the extraction labels
  (`scripts/build_rag_cases.py`, `evals/rag_report_cases.jsonl`, kept in sync by a test). There
  is one case per report with a labelled Scope 1 figure, minus Salzgitter, whose text layer
  garbles it:
  - The owner asks in the report's language, for example "What were BASF's gross Scope 1 GHG
    emissions in 2024?". The answer must contain the figure as printed and cite that report on
    a labelled page.
  - The other tenant asks the same question. It must be declined, and any citation of the
    report counts as a leak.
- **Retrieval.** Every GHG table looks alike, so the company name is resolved before retrieval.
  A question that names a company searches only that company's reports (`ReportNames`), through
  a metadata filter applied together with the tenant filter, also inside the BigQuery query.
  The tenant filter and BigQuery row access policies still decide what a tenant can see at all.
- **Answering.** The extractive model quotes one sentence or table row with its chunk id. Among
  equally matching rows, it prefers a row with figures over headings and prose. Then the
  citation check rejects any sentence without a citation, and any citation of a chunk that was
  not retrieved.

## What fails

The 12 misses are of three kinds:

- **Citation on another page.** BASF, EnBW, K+S, Merck, MVV and Volkswagen are cited on another
  page that also mentions their Scope 1: a summary, a target table, or a part of the group.
- **The right page, the wrong row.** Continental, Henkel and Mercedes-Benz were cited on the
  right report, but the quoted row lacks the printed figure: it is a sub-row or another table's
  row.
- **Declined.** Aurubis, BMW and Siemens Energy were declined, because their rows do not say
  "gross ... GHG emissions".

These are failures of the model-free extractive reader. An LLM reading the same retrieved
chunks would be measured with the same cases. The 0 leaks hold either way, because they come
from the retrieval filters and the citation check, not from the model.
