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
| `trial.tf` | `trial_mode = true` only: GKE Autopilot; the Looker trial **with two guards that delete it before day 30** |
| `functions/kill_switch/` | The function that detaches billing; its decision logic is unit-tested |

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
5. Test the kill switch with a test budget before relying on it (Google's advice).

## Leaving the trial

Set `trial_mode = false` and apply **before day 90**. This destroys GKE and, if it still exists,
the Looker instance. Then upgrade the billing account, or the project is shut down when the trial ends.

## Looker trial

The Looker (Google Cloud core) trial becomes a paid Standard instance after 30 days. It exists
only inside a window fixed by a date:

1. Create an OAuth web client in the console (APIs & Services → Credentials). Store its id as
   the repository variable `LOOKER_OAUTH_CLIENT_ID` and its secret as the repository secret
   `LOOKER_OAUTH_CLIENT_SECRET`.
2. Set the repository variable `LOOKER_TRIAL_START` to today's UTC date and run Infra. Creating
   the instance takes up to an hour. Then add `<looker_url>/oauth2callback` (Terraform output
   `looker_url`) to the OAuth client's authorised redirect URIs, or sign-in fails.
3. Guard 1: a Cloud Scheduler job deletes the instance 25 days later (`looker_delete_after_hours`).
   Guard 2: every plan after that moment counts the instance as 0, so Terraform deletes it if it
   still exists and can never create a second one. Never move `LOOKER_TRIAL_START` later.
