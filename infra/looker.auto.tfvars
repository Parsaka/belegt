# Looker (Google Cloud core) trial: switched off. On 2026-10-27 Google refused both trial
# editions for this project with quota 0 (LOOKER_CORE_TRIAL: AllocateQuota failed on
# looker.googleapis.com/trial_instances; LOOKER_CORE_TRIAL_STANDARD: TrialStandardInstances-
# PerProjectPerRegion, limit 0 in europe-west1). See docs/adr/0004-looker-trial-quota.md.
# An empty looker_trial_start creates nothing and removes the reaper identity.
looker_oauth_client_id = "477686772719-skd06gnrah8n2c14iimulivlbirlnrkq.apps.googleusercontent.com"
looker_trial_start     = ""
