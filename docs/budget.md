# Budget

**Hard limit: 1.00 EUR per month, never exceeded.** (Lowered from 1.50 EUR on 2026-10-25.)
The budget counts net cost, i.e. what is actually charged after credits.

## Strategy

1. **Build inside the Google Cloud free trial** (300 USD, 90 days). The trial does not charge
   automatically when it ends: the billing account closes unless it is upgraded manually.
   GKE and the Looker trial run only in this window. (Cloud SQL and Dagster were planned and
   dropped: GitHub Actions orchestrates, and the vectors live in BigQuery.)
   Report extraction runs there as a GKE Autopilot Indexed Job (`.github/workflows/reports.yml`):
   Autopilot bills the pods' requests (0.5 vCPU, 2 GiB each) for the minutes they run, and the
   GKE free tier credit covers the fee of one Autopilot cluster. Paid from trial credits.
2. **After the trial, only free-tier services stay on.** Parts that were switched off are
   documented with screenshots and labelled as temporary.
3. The GCP trial is **not** activated until the local pre-trial phase is done, so the 90 days
   are spent on cloud work only.

## Steady state after the trial

Free-tier limits come from the [Google Cloud Free Program](https://docs.cloud.google.com/free/docs/free-cloud-features)
(checked 2026-10-25). The costs below are estimates until measured; README numbers will be
measured.

| Service | Free tier per month | Planned use | Expected cost |
|---|---|---|---|
| BigQuery | 1 TiB queries, 10 GiB storage | < 2 GiB stored; daily query quota caps a month at about 620 GiB | 0 |
| Cloud Run jobs + service (europe-west1, Tier 1) | 240k vCPU-s for jobs; 180k vCPU-s and 2M requests for services | report job (7 tasks, on demand); API with min 0, max 1 instance, CPU only during requests | 0 |
| Cloud Scheduler, Workflows | 3 jobs; 5,000 steps | one monthly run | 0 |
| Secret Manager, Logging, Pub/Sub | 6 versions; 50 GiB; 10 GiB | one secret (API tokens); job and budget logs | 0 |
| Cloud Storage (EU) | free tier only in US regions | about 1 GB, with lifecycle rules | about 0.03 EUR |
| Artifact Registry | 0.5 GB | API image about 1.3 GB (torch and the e5 model inside), report image about 0.2 GB; only the latest version of each is kept | about 0.10 EUR |
| Embeddings | none needed | open-source multilingual model in the container | 0 |
| Gemini on Vertex AI | the free Gemini API tier may not serve EEA users | demo answers only; extraction runs once during the trial | about 0.05–0.20 EUR, capped |

Measured cost comes from the Cloud Billing export (dataset `billing`, enabled once in the
console) and is published weekly by `.github/workflows/cost.yml`.

## Cost guards (built first, in Terraform)

1. No always-on paid resources after the trial: no VMs, Cloud SQL, load balancers or clusters.
2. BigQuery custom daily query quota, a hard stop.
3. Service spend caps for Cloud Run and Gemini/Vertex (Public Preview since July 2026).
4. Public API protection: rate limit, `max-instances=1`, demo token.
5. Budget alerts at 0.25, 0.50 and 1.00 EUR.
6. Billing kill switch at 0.60 EUR (budget → Pub/Sub → function that detaches billing,
   following [Google's pattern](https://docs.cloud.google.com/billing/docs/how-to/disable-billing-with-notifications)).
   Google warns that cost data arrives late, so this is the last line, not the main one.

## Known traps

- **Looker trial:** after 30 days it converts automatically to a paid Standard instance.
  A scheduled job deletes it on day 25, and Terraform refuses to keep or recreate it after that
  date (`infra/README.md`, Looker trial).
- **Cloud SQL (not used):** even when stopped, 10 GB of storage costs about 1.70 USD per month, which is
  above the limit. Vectors move to BigQuery before the trial ends.
- **Load balancer:** about 18 USD per month per forwarding rule; only during the trial.
