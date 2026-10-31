# First full production run (2026-10-26)

Measured on Google Cloud (`europe-west1`) from `main` at commit `bc02fd7`. Every figure below is
copied from the run summaries on the `ops-results` branch; the run ids are the folder names there.

| Step | Run | Result |
|---|---|---|
| Infra apply | `infra-apply/2026-10-26T1756-40373057396` | Success |
| Reports on GKE Autopilot (Indexed Job, one task per report) | `reports/2026-10-26T1802-40373329211` | 6 of 6 tasks complete, none failed |
| Pipeline: load, dbt on BigQuery, RAG eval | `pipeline/2026-10-26T1811-40373020804` | dbt 58 of 58 nodes pass; RAG eval 0 leaks |
| Deploy to Cloud Run and smoke test | `deploy/2026-10-26T1836-40378412139` | Both smoke answers correct |
| Pipeline after the postcode and state changes (2026-10-31, `52fa988`) | `pipeline/2026-10-31T1714-41220503503` | dbt 65 of 65 nodes pass; RAG eval 0 leaks |
| Reports on GKE Autopilot, all 37 reports (2026-10-31, after #28) | `reports/2026-10-31T2306-41249255988` | 37 of 37 tasks complete (`completed=0-36`), none failed |
| Kill-switch drill | `kill-switch-drill/2026-10-26T1801-40373329212` | Failed, see below |
| Kill-switch drill after both fixes | `kill-switch-drill/2026-10-26T2035-40396931372` | `WOULD DETACH billing from belegt-pk-2610` |

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

Stationary installations with a map point (2026-10-31, [pipeline run 41218873049](https://github.com/Parsaka/belegt/actions/runs/41218873049)): 2,064 of 2,195
(94.0 %): 49 at the EEA facility point, 2,015 at the centre of the registry contact postcode
(GeoNames), 131 without a point (no German contact postcode, or one GeoNames does not list).

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
("2024 / 2025") and "Mt CO2e", which the extractor now reads. With both changes all six reports
give Scope 1 and both Scope 2 figures, and thyssenkrupp's come from page 123 in the 2024/2025
column (discover run `reports/2026-10-26T1932-40387025723`).

## What the drill found

The kill-switch drill sends a marked budget message and checks the function's verdict in the
logs. It has found two real defects so far, both of which would have stopped billing from being
detached:

1. The function was not registered as a CloudEvent function, so every message raised
   `TypeError` (fixed in #16).
2. The function's identity could not read the project's billing info: `getProjectBillingInfo`
   needs `resourcemanager.projects.get` on the project, and the billing-account role does not
   include it (fixed by granting `roles/browser` on the project in #17).

After #17 the drill reads the project's billing info and confirms the identity holds
`billing.resourceAssociations.delete` on the billing account, so a real budget message at
0.60 EUR would detach billing.
