# Kill-switch drill: after every Infra apply on main, a workflow sends a marked test
# notification to the budget topic and reads the function's verdict from the logs. The function
# then checks the decision and its detach permission but never detaches (see `belegtDrill` in
# functions/kill_switch/main.py). This identity can only publish to that topic and read logs;
# only jobs in the GitHub environment `drill` can use it.

resource "google_service_account" "drill" {
  account_id   = "kill-switch-drill"
  display_name = "Sends kill-switch drill messages from GitHub Actions"
}

resource "google_service_account_iam_member" "drill_wif" {
  for_each           = local.github_subject_repos
  service_account_id = google_service_account.drill.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "${local.github_subject}${each.value}:environment:drill"
}

resource "google_pubsub_topic_iam_member" "drill_publish" {
  topic  = google_pubsub_topic.budget.id
  role   = "roles/pubsub.publisher"
  member = "serviceAccount:${google_service_account.drill.email}"
}

resource "google_project_iam_member" "drill_logs" {
  project = var.project_id
  role    = "roles/logging.viewer"
  member  = "serviceAccount:${google_service_account.drill.email}"
}
