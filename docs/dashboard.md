# Dashboards

Two consumers of the same dbt marts, each with one job. Google grants this project no Looker
trial instance (quota 0, [ADR 0004](adr/0004-looker-trial-quota.md)), so the LookML is checked
in CI and Looker Studio is the only running dashboard.

| | Looker (trial, private) | Looker Studio (free, public) |
|---|---|---|
| Purpose | Semantic layer in code: LookML in `looker/`, reviewed in pull requests | The public page for the project |
| Definitions | Measures such as match rate and "consistent" are defined once in LookML | Charts read the marts directly; no metric logic of its own |
| Lifetime | No instance: trial quota is 0; the code is ready if quota is granted | Stays; BigQuery free tier and the daily quota cap its queries |

## LookML

`looker/belegt.model.lkml` has three explores: ETS installations (with verified emissions and
the current GLEIF record of the operator), group emissions, and reported versus verified
Scope 1 with a link from every figure to its page in the report. `tests/test_dbt.py` checks
offline that every table and column in LookML exists in the dbt build.

If a Looker instance becomes available, connect it:

1. Admin → Database → Connections → Add: name `belegt`, BigQuery, project `belegt-pk-2610`,
   dataset `marts`, authentication "Application Default Credentials" (the Looker service agent,
   which Terraform gives read access to `marts` only).
2. Develop → Projects → New LookML project `belegt`, starting point "Blank project".
3. Configure Git with this repository's SSH URL; Looker shows a deploy key. Add it under the
   repository's Settings → Deploy keys (read only is enough for production mode).

## Looker Studio

Create the report with the BigQuery marts as data source (the link opens a new report; nothing
is created until you save it):

https://lookerstudio.google.com/reporting/create?c.mode=edit&r.reportName=Belegt%20-%20CO2%20belegt&ds.ds0.connector=bigQuery&ds.ds0.type=TABLE&ds.ds0.projectId=belegt-pk-2610&ds.ds0.datasetId=marts&ds.ds0.tableId=mart_group_emissions&ds.ds0.datasourceName=Group%20emissions

Then add `mart_scope1_consistency` and `dim_installation` as further data sources (Resource →
Manage added data sources → Add). Pages:

1. **Groups:** bar chart of verified Mt per group (latest year), year filter.
2. **Reported vs verified:** table of `mart_scope1_consistency` with status, page and the table
   line; conditional colour on `ets_exceeds_reported`.
3. **Installations:** map of `dim_installation` (lat, lon) coloured by `match_decision`.

Share: File → Share → Manage access → "Anyone with the link can view". Data source credentials
stay the owner's; the 20 GiB daily BigQuery quota is the hard stop for public traffic.
