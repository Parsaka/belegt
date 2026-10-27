# Looker (Google Cloud core) trial. Committed rather than kept in repository variables, so the
# trial window is visible in Git history. Neither value is secret: the client secret stays in the
# repository secret LOOKER_OAUTH_CLIENT_SECRET (TF_VAR_looker_oauth_client_secret).
# Never move looker_trial_start later: the deletion guards in trial.tf count from it.
looker_oauth_client_id = "477686772719-skd06gnrah8n2c14iimulivlbirlnrkq.apps.googleusercontent.com"
looker_trial_start     = "2026-10-27"
