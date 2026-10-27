# 4. No Looker instance: LookML is validated in CI, Looker Studio is the dashboard

Status: accepted, 2026-10-27

## Context

The plan used the Looker (Google Cloud core) trial for the LookML semantic layer, guarded by
two deletion jobs (`infra/trial.tf`). Creating the instance failed twice on 2026-10-27:

| Edition | Error |
|---|---|
| `LOOKER_CORE_TRIAL` | 429 `AllocateQuota failed ... looker.googleapis.com/trial_instances` |
| `LOOKER_CORE_TRIAL_STANDARD` | 429 `Quota limit 'TrialStandardInstancesPerProjectPerRegion' has been exceeded. Limit: 0 in region europe-west1` |

A limit of 0 means Google grants no trial instance to this project; the documented path is to
ask Sales for quota. A paid edition is far above the 1 EUR budget.

## Decision

- `looker_trial_start` is empty, so Terraform creates no instance. The trial code and its guards
  stay, so a granted quota needs only a date.
- The LookML in `looker/` stays the semantic layer in code. CI checks it offline: `lkml` parses
  it, and `tests/test_dbt.py` checks every table, column, field reference and join against the
  dbt build.
- Looker Studio (free, permanent) is the public dashboard (`docs/dashboard.md`).

## Consequences

- No running Looker: the LookML is verified against the warehouse schema but not rendered.
- No cost and no deletion deadline to watch.
