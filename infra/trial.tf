# Resources that exist only during the 90-day free trial (trial_mode = true).
# Before the trial ends: set trial_mode = false and apply. See docs/adr/0002.

# --- GKE Autopilot: runtime for Dagster, PDF parse jobs and the API ------------

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

# --- Cloud SQL: Dagster metadata and the pgvector comparison -------------------
# Smallest shared-core instance, about 9 USD/month: trial only. Even stopped, its storage
# would cost more than the monthly limit.

resource "google_sql_database_instance" "trial" {
  count = var.trial_mode ? 1 : 0

  name                = "belegt-pg"
  database_version    = "POSTGRES_16"
  region              = var.region
  deletion_protection = false

  settings {
    edition           = "ENTERPRISE"
    tier              = "db-f1-micro"
    availability_type = "ZONAL"
    disk_type         = "PD_HDD"
    disk_size         = 10
    disk_autoresize   = false

    ip_configuration {
      ipv4_enabled = true # reached only through the Cloud SQL Auth Proxy, no authorised networks
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }

    backup_configuration {
      enabled = false
    }
  }

  depends_on = [google_project_service.this]
}

# --- Looker trial, deleted automatically before it becomes paid ---------------

locals {
  looker_enabled = var.trial_mode && var.looker_oauth_client_id != ""
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

resource "time_static" "looker_created" {
  count = local.looker_enabled ? 1 : 0

  triggers = {
    instance = google_looker_instance.trial[0].id
  }
}

resource "time_offset" "looker_delete_at" {
  count = local.looker_enabled ? 1 : 0

  base_rfc3339 = time_static.looker_created[0].rfc3339
  offset_hours = var.looker_delete_after_hours
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
  schedule = "0 6 ${time_offset.looker_delete_at[0].day} ${time_offset.looker_delete_at[0].month} *"

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
