# Steady state after the trial: the API as a Cloud Run service and the report extraction as a
# Cloud Run job, both inside the free tier (europe-west1 is a Tier 1 region).
#
# Terraform owns the configuration; the Deploy workflow only rolls out new images. The first
# image is Google's placeholder until the first deploy.

locals {
  placeholder_image = "us-docker.pkg.dev/cloudrun/container/hello"
  report_count      = length(csvdecode(file("${path.module}/../dbt/seeds/reports.csv")))
}

# --- API ----------------------------------------------------------------------

resource "google_service_account" "api" {
  account_id   = "belegt-api"
  display_name = "Belegt API on Cloud Run: answers as the tenant of each request's token"
}

# The API reads `rag` only through the tenant identities, so the row access policies apply.
resource "google_service_account_iam_member" "api_acts_as_tenant" {
  for_each = google_service_account.rag_tenant

  service_account_id = each.value.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:${google_service_account.api.email}"
}

# Demo bearer tokens, one per tenant. Generated here, so they are never typed into a file;
# read them with `gcloud secrets versions access latest --secret=api-tokens`.
resource "random_password" "api_token" {
  for_each = toset(var.rag_tenants)

  length  = 32
  special = false
}

resource "google_secret_manager_secret" "api_tokens" {
  secret_id = "api-tokens"

  replication {
    user_managed {
      replicas {
        location = var.region
      }
    }
  }

  depends_on = [google_project_service.this]
}

resource "google_secret_manager_secret_version" "api_tokens" {
  secret      = google_secret_manager_secret.api_tokens.id
  secret_data = join(",", [for t in var.rag_tenants : "${random_password.api_token[t].result}:${t}"])
}

resource "google_secret_manager_secret_iam_member" "api_reads_tokens" {
  secret_id = google_secret_manager_secret.api_tokens.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.api.email}"

  depends_on = [time_sleep.ci_resource_iam]
}

resource "google_cloud_run_v2_service" "api" {
  name                = "api"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = false

  template {
    service_account                  = google_service_account.api.email
    max_instance_request_concurrency = 4
    timeout                          = "60s"

    scaling {
      min_instance_count = 0 # no idle cost
      max_instance_count = 1 # one instance bounds the worst case
    }

    containers {
      image = local.placeholder_image

      resources {
        limits = {
          cpu    = "1"
          memory = "2Gi" # torch and the e5 model
        }
        cpu_idle          = true # CPU is billed only while a request runs
        startup_cpu_boost = true
      }

      env {
        name  = "BELEGT_PROJECT"
        value = var.project_id
      }
      env {
        name = "BELEGT_TOKENS"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.api_tokens.secret_id
            version = "latest"
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 5
        failure_threshold     = 24 # the model takes a while to load on a cold start
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].containers[0].image, client, client_version]
  }

  depends_on = [google_secret_manager_secret_iam_member.api_reads_tokens]
}

# Public endpoint; the app itself requires a bearer token and rate-limits each one.
resource "google_cloud_run_v2_service_iam_member" "api_public" {
  name     = google_cloud_run_v2_service.api.name
  location = google_cloud_run_v2_service.api.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# --- Report extraction job ------------------------------------------------------

resource "google_service_account" "reports_job" {
  account_id   = "reports-job"
  display_name = "Report extraction tasks on Cloud Run (after the trial)"
}

resource "google_storage_bucket_iam_member" "reports_job" {
  bucket = google_storage_bucket.reports.name
  role   = "roles/storage.objectUser"
  member = "serviceAccount:${google_service_account.reports_job.email}"

  depends_on = [time_sleep.ci_resource_iam]
}

resource "google_cloud_run_v2_job" "reports" {
  name                = "reports"
  location            = var.region
  deletion_protection = false

  template {
    task_count  = local.report_count # one task per seed row (CLOUD_RUN_TASK_INDEX)
    parallelism = 2

    template {
      service_account = google_service_account.reports_job.email
      max_retries     = 2
      timeout         = "1800s"

      containers {
        image = local.placeholder_image
        args = [
          "--seed=/app/reports.csv",
          "--work=/tmp/work",
          "--out=gs://${google_storage_bucket.reports.name}/extracted",
          "--pdf-out=gs://${google_storage_bucket.reports.name}",
        ]

        resources {
          limits = {
            cpu    = "1"
            memory = "2Gi"
          }
        }
      }
    }
  }

  lifecycle {
    ignore_changes = [template[0].template[0].containers[0].image, client, client_version]
  }
}

# --- Deploys from GitHub Actions (pipeline identity) ---------------------------

resource "google_project_iam_member" "pipeline_run_deploy" {
  project = var.project_id
  role    = "roles/run.developer" # new revisions and job executions; no IAM changes
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_service_account_iam_member" "pipeline_acts_as_runtime" {
  for_each = {
    api     = google_service_account.api.name
    reports = google_service_account.reports_job.name
  }

  service_account_id = each.value
  role               = "roles/iam.serviceAccountUser"
  member             = "serviceAccount:${google_service_account.pipeline.email}"
}

# The Reports workflow reads the job's result lines from Cloud Logging.
resource "google_project_iam_member" "pipeline_logs" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

# The deploy smoke test calls the API with tenant A's token.
resource "google_secret_manager_secret_iam_member" "pipeline_reads_tokens" {
  secret_id = google_secret_manager_secret.api_tokens.id
  role      = "roles/secretmanager.secretAccessor"
  member    = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [time_sleep.ci_resource_iam]
}

output "api_url" {
  value = google_cloud_run_v2_service.api.uri
}

# The Cost workflow reads the billing export to publish the measured monthly cost.
resource "google_bigquery_dataset_iam_member" "pipeline_billing_read" {
  dataset_id = google_bigquery_dataset.this["billing"].dataset_id
  role       = "roles/bigquery.dataViewer"
  member     = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [time_sleep.ci_resource_iam]
}
