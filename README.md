# Belegt

Sustainability data for German companies, with every number traceable to its source.

Belegt links the verified CO₂ emissions of individual installations in the EU Emissions Trading
System to the companies that own them (through GLEIF ownership data). It also extracts the
figures companies publish in their sustainability statements, citing the page, and flags
inconsistencies between the two. A multi-tenant assistant answers questions with citations, and
it declines to answer when the documents do not contain the answer.

A personal portfolio project (Parsa Kamali). Not investment, audit or legal advice.

**Status:** every phase is built. The cost guards run on Google Cloud (budget with alerts,
billing kill switch, BigQuery daily quota). The full German data loads and passes every dbt test:
2,195 stationary ETS installations, 77.3 % of them matched to a GLEIF company, and 91.7 % of
all 2025 verified tonnage attributed to a company ([measured](docs/measurements/full-data.md)).
What runs where, and what still waits for a merge or a cloud apply, is in
[docs/roadmap.md](docs/roadmap.md#status-2026-10-25).

## How it fits together

| Layer | Tool | Job |
|---|---|---|
| Ingest | Python (`belegt extract`, `belegt reports`) | Download the registries and reports, parse them, keep a manifest with checksums |
| Warehouse | BigQuery (DuckDB locally and in CI) | Raw tables, loaded idempotently |
| Models | dbt | Star schema, SCD2 legal entities, time-bounded ownership bridge, entity resolution, consistency checks |
| Parallel work | Kubernetes Indexed Job (GKE during the trial), Cloud Run job afterwards | One task per sustainability statement; tested on kind in CI |
| Documents | BigQuery `VECTOR_SEARCH`, row access policies | Cited answers per tenant; evals fail CI on any cross-tenant leak |
| Semantic layer | LookML (Looker trial), Looker Studio (public) | Business definitions in code; the public dashboard |
| API | FastAPI on Cloud Run (min 0, max 1) | Bearer token per tenant, rate-limited |
| Infra and CI/CD | Terraform, GitHub Actions with Workload Identity Federation | No keys anywhere; every apply is approved |

## Hard budget

At most **1.00 EUR per month**, enforced in Terraform with several layers. See
[docs/budget.md](docs/budget.md). The build runs inside the Google Cloud free trial. Afterwards
only free-tier services stay on, and parts that were switched off are documented with
screenshots and labelled as temporary.

## Data

Every dataset, with its source, licence and terms, is listed in
[docs/data-sources.md](docs/data-sources.md).

## Development

```bash
pip install -e ".[dev]"
make lint test
belegt sources        # list the registered data sources and their licences
```
