# Raw files: one bucket, immutable inputs. Free tier storage exists only in US regions, so this
# costs a few cents per GB in the EU. Keep it small.
resource "google_storage_bucket" "raw" {
  name                        = "${var.project_id}-raw"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  lifecycle_rule {
    condition {
      days_since_noncurrent_time = 7
    }
    action {
      type = "Delete"
    }
  }

  # Monthly extracts are kept for a year of lineage, then deleted (EU storage is not free).
  lifecycle_rule {
    condition {
      age            = 365
      matches_prefix = ["extracts/"]
    }
    action {
      type = "Delete"
    }
  }

  depends_on = [google_project_service.this]
}

# Sustainability reports are copyrighted: private bucket, never public.
resource "google_storage_bucket" "reports" {
  name                        = "${var.project_id}-reports"
  location                    = var.region
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = false

  depends_on = [google_project_service.this]
}

resource "google_artifact_registry_repository" "images" {
  repository_id = "belegt"
  location      = var.region
  format        = "DOCKER"

  # The free tier is 0.5 GB and the API image (torch and the e5 model) is about 1.3 GB alone:
  # keep only the most recent version of each image. A rollback is a rebuild of an older commit.
  cleanup_policy_dry_run = false
  cleanup_policies {
    id     = "keep-latest"
    action = "KEEP"
    most_recent_versions {
      keep_count = 1
    }
  }
  cleanup_policies {
    id     = "delete-rest"
    action = "DELETE"
    condition {
      tag_state = "ANY"
    }
  }

  depends_on = [google_project_service.this]
}
