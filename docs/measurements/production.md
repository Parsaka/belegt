# First full production run (2026-10-26)

Measured on Google Cloud (`europe-west1`) from `main` at commit `bc02fd7`. Every figure below is
copied from the run summaries on the `ops-results` branch; the run ids are the folder names there.

| Step | Run | Result |
|---|---|---|
| Infra apply | `infra-apply/2026-10-26T1756-40373057396` | Success |
| Reports on GKE Autopilot (Indexed Job, one task per report) | `reports/2026-10-26T1802-40373329211` | 6 of 6 tasks complete, none failed |
| Pipeline: load, dbt on BigQuery, RAG eval | `pipeline/2026-10-26T1811-40373020804` | dbt 58 of 58 nodes pass; RAG eval 0 leaks |
| Deploy to Cloud Run and smoke test | `deploy/2026-10-26T1836-40378412139` | Both smoke answers correct |
| Kill-switch drill | `kill-switch-drill/2026-10-26T1801-40373329212` | Failed, see below |

## Warehouse (BigQuery)

| Model | Rows |
|---|---|
| `dim_installation` | 2,404 |
| `fct_verified_emissions` | 43,272 |
| `dim_legal_entity` | 310,590 |
| `bridge_ownership` | 344,064 |
| `mart_group_emissions` | 11,969 |
| `review_entity_matches` | 113 |

Stationary installations matched to a company: 1,697 of 2,195, the same as the DuckDB run in
[full-data.md](full-data.md).

## Document assistant on BigQuery `VECTOR_SEARCH`

| Metric | Result |
|---|---|
| Answered correctly, citing the right document | 2/2 |
| Abstained correctly | 3/3 |
| Cited another tenant's document | 0 |

## API on Cloud Run (min 0, max 1 instances)

| Request | Seconds |
|---|---|
| First after deploy (cold start) | 3.34 |
| Second (warm) | 1.33 |

## Sustainability statements

Scope figures selected by the extractor, with the page they came from, are in the run's
`summary-gke/reports.md`. Five of six reports gave Scope 1 and Scope 2 figures. thyssenkrupp's
2023/2024 report has no emissions table (it predates the company's first CSRD statement), so the
seed now points at the 2024/2025 annual report. Its E1-6 table uses fiscal-year columns
("2024 / 2025") and "Mt CO2e", which the extractor now reads.

## What the drill found

The kill-switch drill sends a marked budget message and checks the function's verdict in the
logs. It has found two real defects so far, both of which would have stopped billing from being
detached:

1. The function was not registered as a CloudEvent function, so every message raised
   `TypeError` (fixed in #16).
2. The function's identity could not read the project's billing info: `getProjectBillingInfo`
   needs `resourcemanager.projects.get` on the project, and the billing-account role does not
   include it (fixed by granting `roles/browser` on the project).
