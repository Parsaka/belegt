# Permissions the Terraform identity grants itself for resource-level IAM.
#
# roles/editor (from bootstrap_gcp.sh) can create buckets, datasets and repositories but not
# change who may use them (setIamPolicy). These roles add exactly that. The sleep covers IAM
# propagation, so the first apply that needs them does not fail with a 403.

locals {
  ci_resource_iam_roles = [
    "roles/artifactregistry.admin", # repository IAM
    "roles/bigquery.dataOwner",     # dataset IAM
    "roles/storage.admin",          # bucket IAM
  ]
}

resource "google_project_iam_member" "ci_resource_iam" {
  for_each = toset(local.ci_resource_iam_roles)

  project = var.project_id
  role    = each.value
  member  = "serviceAccount:${var.ci_service_account_email}"
}

resource "time_sleep" "ci_resource_iam" {
  create_duration = "90s"
  depends_on      = [google_project_iam_member.ci_resource_iam]
}
