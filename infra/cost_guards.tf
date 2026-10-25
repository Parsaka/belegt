# Cost guards. Built before anything else; see docs/budget.md.
#
# Layer 1 is architectural (no always-on paid resources after the trial) and layer 2 is the
# BigQuery daily quota in bigquery.tf. This file holds the budget, its alerts and the billing
# kill switch. Service spend caps (Cloud Run, Gemini) are in Public Preview without Terraform
# support and are set by hand; see infra/README.md.

locals {
  budget_units = floor(var.budget_amount)
  budget_nanos = floor((var.budget_amount - floor(var.budget_amount)) * 1e9)
  # Alerts at 0.25 and 0.50 EUR, the kill switch at 0.60 EUR, and 1.00 EUR for the default
  # budget. The kill switch fires well below the limit because cost data arrives late.
  alert_fractions = [0.25, 0.5, var.kill_switch_fraction, 1.0]
}

resource "google_pubsub_topic" "budget" {
  name = "budget-alerts"

  depends_on = [google_project_service.this]
}

# Linking a budget to a Pub/Sub topic needs pubsub.topics.setIamPolicy, because the Budget API
# grants its own publisher on the topic. roles/editor does not carry it, so the first apply
# failed with "403 The caller does not have permission". The CI account can only grant this at
# project level (it is a project IAM admin, not a topic admin).
resource "google_project_iam_member" "ci_pubsub_admin" {
  project = var.project_id
  role    = "roles/pubsub.admin"
  member  = "serviceAccount:${var.ci_service_account_email}"
}

# IAM changes take up to a minute to reach the Budget API.
resource "time_sleep" "ci_pubsub_admin" {
  create_duration = "90s"

  depends_on = [google_project_iam_member.ci_pubsub_admin]
}

resource "google_billing_budget" "monthly" {
  billing_account = var.billing_account_id
  display_name    = "belegt hard limit"

  budget_filter {
    projects = ["projects/${data.google_project.this.number}"]
    # Net cost, i.e. what is actually charged. During the trial the 300 USD credit covers
    # usage, so GKE and Looker do not trip the kill switch; afterwards there are no credits.
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
    calendar_period        = "MONTH"
  }

  amount {
    specified_amount {
      currency_code = var.budget_currency
      units         = tostring(local.budget_units)
      nanos         = local.budget_nanos
    }
  }

  dynamic "threshold_rules" {
    for_each = local.alert_fractions
    content {
      threshold_percent = threshold_rules.value
      spend_basis       = "CURRENT_SPEND"
    }
  }

  all_updates_rule {
    pubsub_topic                    = google_pubsub_topic.budget.id
    schema_version                  = "1.0"
    disable_default_iam_recipients  = false
    enable_project_level_recipients = true
  }

  depends_on = [time_sleep.ci_pubsub_admin]
}

# --- kill switch: budget notification -> function -> detach billing ------------

resource "google_service_account" "kill_switch" {
  account_id   = "kill-switch"
  display_name = "Detaches billing when spend reaches the kill-switch threshold"
}

# Google's documented pattern grants Billing Account Administrator to this identity.
resource "google_billing_account_iam_member" "kill_switch" {
  billing_account_id = var.billing_account_id
  role               = "roles/billing.admin"
  member             = "serviceAccount:${google_service_account.kill_switch.email}"
}

data "archive_file" "kill_switch" {
  type        = "zip"
  source_dir  = "${path.module}/functions/kill_switch"
  output_path = "${path.module}/.build/kill_switch.zip"
  excludes    = ["__pycache__"]
}

resource "google_storage_bucket" "functions" {
  name                        = "${var.project_id}-functions"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = true

  depends_on = [google_project_service.this]
}

resource "google_storage_bucket_object" "kill_switch" {
  name   = "kill_switch-${data.archive_file.kill_switch.output_md5}.zip"
  bucket = google_storage_bucket.functions.name
  source = data.archive_file.kill_switch.output_path
}

resource "google_cloudfunctions2_function" "kill_switch" {
  name     = "kill-switch"
  location = var.region

  build_config {
    runtime     = "python312"
    entry_point = "stop_billing"
    source {
      storage_source {
        bucket = google_storage_bucket.functions.name
        object = google_storage_bucket_object.kill_switch.name
      }
    }
  }

  service_config {
    max_instance_count    = 1
    min_instance_count    = 0
    available_memory      = "256M"
    timeout_seconds       = 60
    service_account_email = google_service_account.kill_switch.email
    environment_variables = {
      GCP_PROJECT_ID       = var.project_id
      KILL_SWITCH_FRACTION = tostring(var.kill_switch_fraction)
    }
  }

  event_trigger {
    trigger_region        = var.region
    event_type            = "google.cloud.pubsub.topic.v1.messagePublished"
    pubsub_topic          = google_pubsub_topic.budget.id
    retry_policy          = "RETRY_POLICY_RETRY"
    service_account_email = google_service_account.kill_switch.email
  }
}

resource "google_project_iam_member" "kill_switch_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.kill_switch.email}"
}
