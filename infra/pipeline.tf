# The data pipeline's identity: least privilege, separate from the Terraform service account.
#
# Only jobs of this repository that run in the GitHub environment `pipeline` can impersonate it
# (the OIDC subject is repo:<owner>/<repo>:environment:pipeline), so a workflow on another branch
# without that environment gets nothing.

locals {
  pipeline_datasets = ["raw", "staging", "snapshots", "marts"]
  pipeline_subject  = "principal://iam.googleapis.com/projects/${data.google_project.this.number}/locations/global/workloadIdentityPools/github/subject/repo:${var.github_repository}:environment:pipeline"
}

resource "google_service_account" "pipeline" {
  account_id   = "pipeline"
  display_name = "Monthly extract, BigQuery load and dbt build from GitHub Actions"
}

resource "google_service_account_iam_member" "pipeline_wif" {
  service_account_id = google_service_account.pipeline.name
  role               = "roles/iam.workloadIdentityUser"
  member             = local.pipeline_subject
}

# Run load and query jobs; the daily query quota in bigquery.tf caps what they can cost.
resource "google_project_iam_member" "pipeline_jobs" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_bigquery_dataset_iam_member" "pipeline" {
  for_each = toset(local.pipeline_datasets)

  dataset_id = google_bigquery_dataset.this[each.key].dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

# The extracts are written to the raw bucket under extracts/<date>/ for lineage.
resource "google_storage_bucket_iam_member" "pipeline_raw" {
  bucket = google_storage_bucket.raw.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.pipeline.email}"
}

output "pipeline_service_account" {
  value = google_service_account.pipeline.email
}
