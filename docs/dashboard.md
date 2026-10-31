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

**Live report:** https://lookerstudio.google.com/reporting/8653329c-9086-4395-9526-c577d32895fb
(view only; data from `belegt-pk-2610.marts` with the owner's credentials).

Three pages share one theme (accent `#1b5e20`), a header with the subtitle "EU ETS verified
emissions vs. company-reported Scope 1, German groups", and a footer with sources and the repo.

| Page | Source | Content | Figures shown on 2026-10-31 |
|---|---|---|---|
| Groups | `mart_group_emissions` | Year (default 2025) and group filters, KPIs, top 15 groups in Mt, table with LEI | 609 groups, 248.8 Mt CO2e, 1,392 installations (2025) |
| Reported vs verified | `mart_scope1_consistency` | Reported (grey) vs ETS (green) per report, explanation, table with page and quote, red/green status | 6 reports, 0 contradictions, mean ETS share 53 % |
| Installations | `dim_installation` | Map coloured by `match_decision`, kind and match filters, table | 2,195 stationary installations |

Known gaps visible in the report:

- Only 49 of 2,398 installations have EEA coordinates, so the map is sparse.
- ETS covers German installations only, so a group's ETS share of its global Scope 1 can be
  small (Heidelberg Materials 4.9 %) without being a contradiction.
- The year control defaults to one year: group installation counts would otherwise add up
  across years.

To rebuild it from scratch, open the create link (nothing is saved until you save it):

https://lookerstudio.google.com/reporting/create?c.mode=edit&r.reportName=Belegt%20-%20CO2%20belegt&ds.ds0.connector=bigQuery&ds.ds0.type=TABLE&ds.ds0.projectId=belegt-pk-2610&ds.ds0.datasetId=marts&ds.ds0.tableId=mart_group_emissions&ds.ds0.datasourceName=Group%20emissions

then add `mart_scope1_consistency` and `dim_installation` (Resource → Manage added data
sources → Add). Share: Share → Link settings → "Unlisted", viewer. Data source credentials stay
the owner's; the 20 GiB daily BigQuery quota is the hard stop for public traffic.
