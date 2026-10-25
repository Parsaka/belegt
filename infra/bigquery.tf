locals {
  datasets = {
    raw       = "Raw loads, one table per source file"
    staging   = "dbt staging models"
    snapshots = "dbt snapshots: SCD2 history of GLEIF legal entities"
    marts     = "dbt marts: facts, dimensions, consistency checks"
    rag       = "Document chunks and embeddings, one row access policy per tenant"
  }
}

resource "google_bigquery_dataset" "this" {
  for_each = local.datasets

  dataset_id  = each.key
  description = each.value
  location    = var.bq_location

  depends_on = [google_project_service.this]
}

# Hard stop on query spend: queries fail once a day's quota is used, they are never billed.
resource "google_service_usage_consumer_quota_override" "bq_query_per_day" {
  provider = google-beta

  project        = var.project_id
  service        = "bigquery.googleapis.com"
  metric         = urlencode("bigquery.googleapis.com/quota/query/usage")
  limit          = urlencode("/d/project")
  override_value = tostring(var.bq_daily_query_mib)
  force          = true

  depends_on = [google_project_service.this]
}
