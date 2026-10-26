# Roadmap

Phases are done in order. Each ends with something complete that can be shown.

| Phase | When | Scope | Done when |
|---|---|---|---|
| Pre-trial | 1–2 weeks, local, zero cost | Download and inspect every source; loaders; first dbt models on DuckDB; PDF parser; first eval set | Data and models are ready before the trial clock starts |
| 0 | Trial week 1 | GCP via Terraform, WIF for GitHub Actions, **all cost guards first** | Kill switch tested with a test budget |
| 1 | Weeks 2–4 | BigQuery, dbt marts, SCD2 entities, time-bounded ownership bridge, entity resolution (ETS id path and parent name → GLEIF path) | ERD and dbt docs published |
| 2 | Weeks 5–6 | GKE Autopilot, Helm, parallel PDF parse (Indexed Job), metric extraction with page citations | `fct_reported_metric` filled |
| 3 | Weeks 7–8 | Multi-tenant RAG on BigQuery VECTOR_SEARCH with row access policies; isolation tests and evals in CI | Eval report |
| 4 | Weeks 9–10 | LookML on the Looker trial (auto-deleted before day 30); public Looker Studio dashboard | Dashboard link, screenshots |
| 5 | Weeks 11–12 | Move to steady state: destroy GKE, run on Cloud Run, measure a week of real cost; upgrade before day 90 | Measured cost under 1.00 EUR in the README |

## Status (2026-10-25)

| Phase | Code | Running in the cloud |
|---|---|---|
| 0 | Merged | Applied: budget, alerts, kill switch, query quota. The drill (#9) waits for its merge. |
| 1 | PR #10 | DuckDB run on the full data passes every test ([measured](measurements/full-data.md)); BigQuery after merge and apply |
| 2 | PR #12 | Indexed Job tested on kind in CI; the extractor runs on the seven real reports in CI; GKE after `TRIAL_MODE` |
| 3 | PR #11 | Offline evals pass; BigQuery evals after merge and apply |
| 4 | PR #13 | LookML validated offline against the dbt build; Looker needs an OAuth client and `LOOKER_TRIAL_START` |
| 5 | PR #14 | Cloud Run service and job, Deploy smoke test, Cost workflow; cost measured once the billing export is on |
