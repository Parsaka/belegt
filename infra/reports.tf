# Sustainability reports: the image registry for the extraction tasks, and who may read and
# write the private reports bucket.
#
# During the trial the tasks run as a Kubernetes Indexed Job on GKE Autopilot. The pods use
# GKE Workload Identity: IAM grants the bucket to the Kubernetes service account belegt/reports
# directly, so there is no Google service account key and no annotation to keep in sync.

locals {
  reports_ksa = "principal://iam.googleapis.com/projects/${data.google_project.this.number}/locations/global/workloadIdentityPools/${var.project_id}.svc.id.goog/subject/ns/belegt/sa/reports"
}

# The pipeline builds and pushes the task image (also used by the Cloud Run job after the trial).
resource "google_artifact_registry_repository_iam_member" "pipeline_push" {
  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.writer"
  member     = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [time_sleep.ci_resource_iam]
}

# The pipeline loads the extracted figures (extracted/metrics/*.jsonl) into BigQuery.
resource "google_storage_bucket_iam_member" "pipeline_reports_read" {
  bucket = google_storage_bucket.reports.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.pipeline.email}"

  depends_on = [time_sleep.ci_resource_iam]
}

# --- trial only: GKE --------------------------------------------------------------

# Submit the Job to the cluster (Kubernetes objects only; no cluster administration).
resource "google_project_iam_member" "pipeline_gke" {
  count = var.trial_mode ? 1 : 0

  project = var.project_id
  role    = "roles/container.developer"
  member  = "serviceAccount:${google_service_account.pipeline.email}"
}

resource "google_storage_bucket_iam_member" "reports_tasks" {
  count = var.trial_mode ? 1 : 0

  bucket = google_storage_bucket.reports.name
  role   = "roles/storage.objectUser" # read and write objects, no bucket settings or IAM
  member = local.reports_ksa

  # the identity pool exists once the cluster does
  depends_on = [google_container_cluster.trial, time_sleep.ci_resource_iam]
}

# Autopilot nodes run as the Compute Engine default service account and pull the image.
resource "google_artifact_registry_repository_iam_member" "nodes_pull" {
  count = var.trial_mode ? 1 : 0

  location   = google_artifact_registry_repository.images.location
  repository = google_artifact_registry_repository.images.name
  role       = "roles/artifactregistry.reader"
  member     = "serviceAccount:${data.google_project.this.number}-compute@developer.gserviceaccount.com"

  depends_on = [google_container_cluster.trial, time_sleep.ci_resource_iam]
}
