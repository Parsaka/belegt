terraform {
  required_version = ">= 1.9"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 8.8"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 8.8"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.8"
    }
    time = {
      source  = "hashicorp/time"
      version = "~> 0.14"
    }
  }

  # Bucket and prefix come from backend.hcl, written by scripts/bootstrap_gcp.sh.
  backend "gcs" {}
}

provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}
