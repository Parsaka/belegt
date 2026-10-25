# Resources that exist only during the 90-day free trial (trial_mode = true).
# Cloud SQL is not among them: orchestration is GitHub Actions and vectors live in BigQuery.
# Before the trial ends: set trial_mode = false and apply. See docs/adr/0002.

# --- GKE Autopilot: runtime for the report Indexed Job (reports.yml) -------------

resource "google_container_cluster" "trial" {
  count = var.trial_mode ? 1 : 0

  name                = "belegt"
  location            = var.region
  enable_autopilot    = true
  deletion_protection = false

  release_channel {
    channel = "REGULAR"
  }

  depends_on = [google_project_service.this]
}

# --- Looker trial, deleted automatically before it becomes paid ---------------

# The trial window is fixed by a date, not by the instance: `looker_trial_start` (set once, when
# the trial is started) plus `looker_delete_after_hours`. Two independent guards end it:
# 1. a Cloud Scheduler job deletes the instance on the deletion day;
# 2. any Terraform plan after that time counts the instance as 0, so Terraform deletes it if it
#    still exists and never creates a second one (which would not be a trial).
locals {
  looker_delete_at = (
    var.looker_trial_start == "" ? null :
    timeadd("${var.looker_trial_start}T00:00:00Z", "${var.looker_delete_after_hours}h")
  )
  looker_enabled = (
    var.trial_mode && var.looker_oauth_client_id != "" && local.looker_delete_at != null
    ? timecmp(plantimestamp(), local.looker_delete_at) < 0
    : false
  )
}

resource "google_looker_instance" "trial" {
  count = local.looker_enabled ? 1 : 0

  name             = "belegt"
  region           = var.region
  platform_edition = "LOOKER_CORE_TRIAL"

  oauth_config {
    client_id     = var.looker_oauth_client_id
    client_secret = var.looker_oauth_client_secret
  }

  depends_on = [google_project_service.this]
}

resource "google_service_account" "looker_reaper" {
  count = local.looker_enabled ? 1 : 0

  account_id   = "looker-reaper"
  display_name = "Deletes the Looker trial before it converts to a paid instance"
}

resource "google_project_iam_member" "looker_reaper" {
  count = local.looker_enabled ? 1 : 0

  project = var.project_id
  role    = "roles/looker.admin"
  member  = "serviceAccount:${google_service_account.looker_reaper[0].email}"
}

resource "google_cloud_scheduler_job" "looker_reaper" {
  count = local.looker_enabled ? 1 : 0

  name      = "delete-looker-trial"
  region    = var.region
  time_zone = "Etc/UTC"
  # A fixed date (minute hour day month): fires once on the deletion day.
  schedule = "${formatdate("m H D M", local.looker_delete_at)} *"

  http_target {
    http_method = "DELETE"
    uri         = "https://looker.googleapis.com/v1/${google_looker_instance.trial[0].id}?force=true"

    oauth_token {
      service_account_email = google_service_account.looker_reaper[0].email
    }
  }

  retry_config {
    retry_count = 5
  }
}

# Looker reads the marts with its own service agent (an "Application Default Credentials"
# connection in Looker): read-only, marts only. The daily BigQuery quota caps its queries.
resource "google_bigquery_dataset_iam_member" "looker_marts" {
  count = local.looker_enabled ? 1 : 0

  dataset_id = google_bigquery_dataset.this["marts"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-looker.iam.gserviceaccount.com"

  depends_on = [google_looker_instance.trial, time_sleep.ci_resource_iam]
}

resource "google_project_iam_member" "looker_jobs" {
  count = local.looker_enabled ? 1 : 0

  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:service-${data.google_project.this.number}@gcp-sa-looker.iam.gserviceaccount.com"

  depends_on = [google_looker_instance.trial]
}
