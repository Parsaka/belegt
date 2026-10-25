# Belegt – guide for Claude Code

Portfolio project: ESG data platform for German companies on Google Cloud.
Sources: EU ETS verified emissions (Union Registry), EEA Industrial Reporting (IED/E-PRTR),
GLEIF LEI + Level 2 relationships, ESRS text (EUR-Lex), sustainability statements (PDF).
Stack: Python loaders → GCS → BigQuery (dbt Core, star schema with SCD2 and entity resolution)
→ LookML / Looker Studio. Document pipeline: PDF parse + open-source embeddings → BigQuery
VECTOR_SEARCH with row access policies per tenant → RAG API with citations and abstention.
Runtime: GKE Autopilot during the GCP free trial, Cloud Run afterwards; Kubernetes is always
tested with kind in CI. Infra with Terraform, CI/CD with GitHub Actions (Workload Identity
Federation, no keys).

## Hard constraints
- **Budget: at most 1.50 EUR/month, never exceeded.** The build runs inside the GCP 300 USD /
  90-day free trial. After the trial, only free-tier services may stay on. Every resource must be
  listed in `docs/budget.md` with its free-tier limit and expected cost; ask before adding
  anything that is not there. Cost guards (daily BigQuery query quota, service spend caps,
  budget alerts, billing kill switch at 1.20 EUR) are part of the Terraform and are built first.
- No always-on paid resources after the trial: no VMs, Cloud SQL, load balancers or GKE clusters.
  Cloud Run uses `min-instances=0`, `max-instances=1`.
- **Looker trial auto-converts to a paid Standard instance after 30 days.** It must be deleted
  automatically before day 30. Never create a Looker instance without that deletion job.
- Do not activate the GCP trial or create cloud resources before the pre-trial phase is done.
- Python 3.11+, `src/` layout, package `belegt`. ruff + mypy + pytest. Small PRs per phase
  (`docs/roadmap.md`).
- Writes are idempotent; re-runs overwrite.
- Tests never hit the network (`@pytest.mark.live` for the few that do; skipped in CI). Fixtures are
  trimmed real files in `tests/fixtures/`.
- Sustainability reports are copyrighted: PDFs live only in a private bucket or local `data/`;
  Git holds links and metadata only.
- No secrets in Git: `.env` locally, Secret Manager / WIF in the cloud.
- Every dataset has source + licence in `docs/data-sources.md` and in `belegt.sources`.
  Send an informative User-Agent.
- One tool, one job: do not add a technology that duplicates an existing one's role.
- README numbers must be measured, never estimated.

## Commands
- `pip install -e ".[dev]"` · `pytest` · `ruff check . && ruff format .` · `mypy`
- `belegt sources`
