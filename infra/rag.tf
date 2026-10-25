# Document assistant: one identity per tenant. Queries for a tenant run as its identity, and
# the row access policy on rag.chunks (created by `belegt rag-load`) lets that identity see only
# the tenant's rows and the shared corpus. Without a policy an identity sees no rows at all.

resource "google_service_account" "rag_tenant" {
  for_each = toset(var.rag_tenants)

  account_id   = "rag-${replace(each.key, "_", "-")}"
  display_name = "Document assistant, tenant ${each.key}"
}

resource "google_bigquery_dataset_iam_member" "rag_tenant_read" {
  for_each = google_service_account.rag_tenant

  dataset_id = google_bigquery_dataset.this["rag"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${each.value.email}"
}

resource "google_project_iam_member" "rag_tenant_jobs" {
  for_each = google_service_account.rag_tenant

  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${each.value.email}"
}

# The pipeline loads the chunks, creates the policies (data owner on `rag` only) and runs the
# isolation evals as each tenant.
resource "google_bigquery_dataset_iam_member" "pipeline_rag_owner" {
  dataset_id = google_bigquery_dataset.this["rag"].dataset_id
  role       = "roles/bigquery.dataOwner"
  member     = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_service_account_iam_member" "pipeline_acts_as_tenant" {
  for_each = google_service_account.rag_tenant

  service_account_id = each.value.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.pipeline.email}"
}
