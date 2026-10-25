# Infrastructure

Terraform for Google Cloud. Nothing is applied until the pre-trial phase is done and the free
trial is active. The order matters: the cost guards come first.

## Files

| File | What |
|---|---|
| `cost_guards.tf` | Budget (1.50 EUR) with alerts at 0.50 / 1.00 / 1.20, Pub/Sub topic, billing kill switch |
| `bigquery.tf` | Datasets `raw`, `staging`, `marts`, `rag`; **daily query quota** (hard stop) |
| `storage.tf` | Raw and reports buckets (private), Artifact Registry with a keep-two cleanup policy |
| `trial.tf` | `trial_mode = true` only: GKE Autopilot, Cloud SQL, Looker trial **with automatic deletion before day 30** |
| `functions/kill_switch/` | The function that detaches billing; its decision logic is unit-tested |

## First run

1. The owner activates the GCP free trial and creates a project.
2. In Cloud Shell: `PROJECT_ID=... BILLING_ACCOUNT_ID=... bash scripts/bootstrap_gcp.sh`.
   This creates the state bucket, a CI service account and Workload Identity Federation that
   trusts only this repository. No keys.
3. Store the printed values as GitHub repository variables. The `Infra` workflow then plans on
   every pull request and applies on `main` (after approval of the `gcp` environment).
4. **Set by hand (Public Preview, no Terraform support yet):** service spend caps for Cloud Run
   and Gemini / Vertex AI under Billing → Budgets, about 0.30 EUR each.
5. Test the kill switch with a test budget before relying on it (Google's advice).

## Leaving the trial

Set `trial_mode = false` and apply **before day 90**. This destroys GKE, Cloud SQL and the Looker
instance. Then upgrade the billing account, or the project is shut down when the trial ends.
