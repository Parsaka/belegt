# Infrastructure

Terraform for Google Cloud. Nothing is applied until the pre-trial phase is done and the free
trial is active. The order matters: the cost guards come first.

## Files

| File | What |
|---|---|
| `cost_guards.tf` | Budget (1.00 EUR, net of credits) with alerts at 0.25 / 0.50 / 1.00, Pub/Sub topic, billing kill switch at 0.60 |
| `bigquery.tf` | Datasets `raw`, `staging`, `marts`, `rag`; **daily query quota** (hard stop) |
| `storage.tf` | Raw and reports buckets (private), Artifact Registry with a keep-two cleanup policy |
| `ci_permissions.tf` | Resource-level IAM roles the Terraform identity grants itself (Editor cannot set bucket, dataset or repository IAM) |
| `pipeline.tf`, `rag.tf`, `reports.tf`, `drill.tf` | Least-privilege identities: the pipeline, one per RAG tenant, the report pods (GKE Workload Identity), the kill-switch drill |
| `cloud_run.tf` | Steady state: the API (min 0, max 1 instance, generated demo tokens in Secret Manager) and the report job; Terraform owns the configuration, the Deploy workflow rolls out images |
| `trial.tf` | `trial_mode = true` only: GKE Autopilot; the Looker trial **with two guards that delete it before day 30** |
| `functions/kill_switch/` | The function that detaches billing; its decision logic is unit-tested |
| `drill.tf` | Identity for the kill-switch drill: publish to the budget topic, read logs |

## First run

1. The owner activates the GCP free trial and creates a project.
2. In Cloud Shell: `PROJECT_ID=... BILLING_ACCOUNT_ID=... bash scripts/bootstrap_gcp.sh`.
   This creates the state bucket, a CI service account and Workload Identity Federation that
   trusts only this repository. No keys. The script is safe to re-run: it skips what exists and
   retries the IAM bindings while a new service account propagates (the first real run hit
   that). Project ids are global, so the first choice may be taken; this project is
   `belegt-pk-2610`.
3. Store the printed values as GitHub repository variables. The `Infra` workflow then plans on
   every pull request and applies on `main` (after approval of the `gcp` environment).
4. **Set by hand (Public Preview, no Terraform support yet):** service spend caps for Cloud Run
   and Gemini / Vertex AI under Billing → Budgets, about 0.30 EUR each.
5. The kill switch is drilled after every apply on main (workflow `Kill-switch drill`): a
   marked message goes to the budget topic, and the function runs the decision, reads billing
   and checks its permission to detach, then stops. The verdict lands on the `ops-results`
   branch. A real detach is tested once by hand, with the owner, because it stops the project.
6. Enable the Cloud Billing export to BigQuery (Billing → Billing export → Standard usage cost →
   project `belegt-pk-2610`, dataset `billing`). It cannot be set up through an API. The Cost
   workflow reads it.

## Leaving the trial

Set `trial_mode = false` and apply **before day 90**. This destroys GKE and, if it still exists,
the Looker instance. Then upgrade the billing account, or the project is shut down when the trial ends.

## Looker trial

The Looker (Google Cloud core) trial becomes a paid Standard instance after 30 days. It exists
only inside a window fixed by a date:

1. Create an OAuth web client in the console (Google Auth Platform → Clients). Its id and the
   trial start date are committed in `looker.auto.tfvars`; its secret is the repository secret
   `LOOKER_OAUTH_CLIENT_SECRET`.
2. Merging that file runs Infra. Creating the instance takes up to an hour. Then add
   `<looker_url>/oauth2callback` (Terraform output `looker_url`) to the OAuth client's authorised
   redirect URIs, or sign-in fails.
3. Guard 1: a Cloud Scheduler job deletes the instance 25 days later (`looker_delete_after_hours`).
   Guard 2: every plan after that moment counts the instance as 0, so Terraform deletes it if it
   still exists and can never create a second one. Never move `looker_trial_start` later.
