output "raw_bucket" {
  value = google_storage_bucket.raw.name
}

output "reports_bucket" {
  value = google_storage_bucket.reports.name
}

output "image_repository" {
  value = "${var.region}-docker.pkg.dev/${var.project_id}/${google_artifact_registry_repository.images.repository_id}"
}

output "budget_topic" {
  value = google_pubsub_topic.budget.id
}

output "looker_delete_at" {
  description = "When the Looker trial is deleted automatically (empty when no Looker trial exists)."
  value       = local.looker_delete_at == null ? "" : local.looker_delete_at
}
