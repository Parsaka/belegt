# Evaluation cases

`rag_cases.jsonl` holds the cases for the document assistant (see `belegt.rag.evals`). Each line
names a tenant, a question and the expected outcome: an answer citing a given document, or an
abstention. A question about another tenant's document must abstain; answering it is a leak.

The tenant memos are synthetic and labelled as such (`deploy/kind/demo-chunks.jsonl`); the
shared corpus is the ESRS (EU legal text, reuse with attribution).

- Offline (CI): `belegt rag-eval --backend memory`
- Cloud: `belegt rag-eval --backend bigquery --project <id>`. Every question then runs as the
  tenant's own service account, so the leak count measures the row access policies.
