variable "project_id" {
  description = "GCP project id."
  type        = string
}

variable "billing_account_id" {
  description = "Billing account id (XXXXXX-XXXXXX-XXXXXX), used by the budget and the kill switch."
  type        = string
}

variable "region" {
  description = "Region for regional resources. europe-west1 is a Tier 1 Cloud Run region."
  type        = string
  default     = "europe-west1"
}

variable "bq_location" {
  description = "BigQuery dataset location."
  type        = string
  default     = "EU"
}

variable "github_repository" {
  description = "owner/repo allowed to deploy through Workload Identity Federation."
  type        = string
  default     = "Parsaka/belegt"
}

variable "ci_service_account_email" {
  description = "Service account that GitHub Actions impersonates (created by scripts/bootstrap_gcp.sh)."
  type        = string
}

# --- cost guards -------------------------------------------------------------

variable "budget_currency" {
  description = "Must equal the billing account currency, or the budget is rejected."
  type        = string
  default     = "EUR"
}

variable "budget_amount" {
  description = "Hard monthly limit. The project must never cost more than this."
  type        = number
  default     = 1.0
}

variable "kill_switch_fraction" {
  description = "Fraction of the budget at which billing is detached (0.6 x 1.00 = 0.60)."
  type        = number
  default     = 0.6

  validation {
    condition     = var.kill_switch_fraction > 0 && var.kill_switch_fraction < 1
    error_message = "The kill switch must fire below the budget, because cost data arrives late."
  }
}

variable "bq_daily_query_mib" {
  description = "Custom BigQuery quota: MiB processed per project per day. 20 GiB x 31 days stays under the 1 TiB free tier."
  type        = number
  default     = 20480
}

# --- trial-only resources ----------------------------------------------------

variable "trial_mode" {
  description = "True only during the 90-day free trial: creates GKE, Cloud SQL and the Looker trial."
  type        = bool
  default     = false
}

variable "looker_oauth_client_id" {
  description = "OAuth web client for the Looker trial instance (created by hand in the console)."
  type        = string
  default     = ""
}

variable "looker_oauth_client_secret" {
  description = "Secret of the OAuth web client above."
  type        = string
  default     = ""
  sensitive   = true
}

variable "looker_delete_after_hours" {
  description = "The Looker trial converts to a paid instance after 30 days. Delete it after 25."
  type        = number
  default     = 600

  validation {
    condition     = var.looker_delete_after_hours <= 648
    error_message = "Delete the Looker trial at most 27 days after creation (it becomes paid on day 30)."
  }
}

variable "rag_tenants" {
  description = "Tenants of the document assistant. Each gets an identity and a row access policy."
  type        = list(string)
  default     = ["tenant_a", "tenant_b"]

  validation {
    condition     = alltrue([for t in var.rag_tenants : can(regex("^[a-z][a-z0-9_]{1,20}$", t)) && t != "shared"])
    error_message = "Tenant ids: a-z, 0-9 and _, 2 to 21 characters, and not 'shared'."
  }
}
