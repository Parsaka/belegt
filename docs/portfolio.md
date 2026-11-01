# Belegt: portfolio brief

This page is the brief for presenting Belegt elsewhere, such as on a personal portfolio website.
Everything here is copied from measured runs. If a number here and a measurement page ever
disagree, the measurement page in `docs/measurements/` is the source.

## Pitch (2-3 sentences)

Belegt checks the climate figures of German companies against independent data. It links the
verified CO₂ emissions of 2,195 EU ETS installations to the corporate groups that own them,
using GLEIF ownership data and entity resolution. It also extracts the Scope 1-3 figures from
37 DAX/MDAX annual reports, citing the page. A multi-tenant document assistant answers
questions about the reports with page citations, and it never shows a tenant another tenant's
documents.

*(German)* Belegt prüft die Klimazahlen deutscher Konzerne gegen unabhängige Daten. Es ordnet die
verifizierten CO₂-Emissionen von 2.195 EU-ETS-Anlagen über GLEIF-Eigentümerdaten und Entity
Resolution ihren Konzernen zu. Außerdem liest es die Scope-1-3-Werte aus 37 DAX/MDAX-Berichten
mit Seitenangabe aus. Ein mandantenfähiger Assistent beantwortet Fragen zu den Berichten mit
Seitenzitaten und zeigt einem Mandanten nie die Dokumente eines anderen.

## Links

- Project page (start here): https://parsaka.github.io/belegt/
- Code and README: https://github.com/Parsaka/belegt
- Dashboard (Looker Studio): https://lookerstudio.google.com/reporting/8653329c-9086-4395-9526-c577d32895fb
- Data model, dbt docs and lineage: https://parsaka.github.io/belegt/dbt/
- Measured results:
  - [extraction accuracy](https://github.com/Parsaka/belegt/blob/main/docs/measurements/extraction.md)
  - [assistant on the reports](https://github.com/Parsaka/belegt/blob/main/docs/measurements/assistant-reports.md)
  - [production run](https://github.com/Parsaka/belegt/blob/main/docs/measurements/production.md)

## Measured results (all from real runs on Google Cloud and GitHub Actions)

- **Installations:** 2,195 German stationary ETS installations. 77.3 % are matched to a GLEIF
  company, and 91.7 % of 2025 verified tonnage is attributed to a group.
- **dbt on BigQuery:** 65 of 65 nodes pass, with an SCD2 snapshot, a bridge table, entity
  resolution and tests.
- **Extraction:** Scope 1-3 extraction on 37 reports against 148 hand labels reaches 82.7 %
  precision and 70.5 % recall, up from 53.7 % and 41.8 %. On the 22 held-out reports,
  precision is 80.8 %.
- **Parsing at scale:** 37 of 37 reports were parsed in parallel by a Kubernetes Indexed Job on
  GKE Autopilot.
- **Document assistant:** 19 of 31 questions were answered with the printed figure and a
  citation on the right page. All 31 of 31 cross-tenant questions were declined, with 0 leaks.
  The result is the same in memory and on BigQuery `VECTOR_SEARCH` with row access policies.
- **API on Cloud Run:** 3.34 s cold start, 1.33 s warm.
- **Cost:** 0.00 EUR net in October 2026, with a hard cap of 1.00 EUR per month, budget alerts,
  a daily BigQuery quota and a tested billing kill switch.

## Tech

Python, BigQuery (dbt Core, VECTOR_SEARCH, row access policies), GCS, GKE Autopilot and kind,
Cloud Run (FastAPI), Terraform, GitHub Actions with Workload Identity Federation (no keys),
LookML and Looker Studio, multilingual-e5 embeddings, pytest, ruff and mypy.

## Skills shown

- **Data modelling:** star schema, SCD2, bridge tables, entity resolution with a review queue.
- **RAG:** citations, abstention, tenant isolation, evals built from labels.
- **Measured evaluation:** dev and test splits, hand labels, before and after numbers.
- **Platform:** IaC, keyless CI/CD, Kubernetes jobs, cost guards that really stop spend.

## Material in this repository

| What | Where |
|---|---|
| Finished project page (story, architecture diagram, deep dives, results, decisions, limits) | [docs/site/index.html](site/index.html), live at https://parsaka.github.io/belegt/ |
| Full technical overview, results table, architecture (Mermaid) | [README.md](../README.md) |
| Data model (ERD) and modelling decisions | [docs/erd.md](erd.md) |
| Measured results with method and run ids | [docs/measurements/](measurements/) |
| Design decisions | [docs/adr/](adr/) |
| Budget and cost guards | [docs/budget.md](budget.md) |
| Data sources and licences (needed for attribution on any public page) | [docs/data-sources.md](data-sources.md) |
| Dashboard description | [docs/dashboard.md](dashboard.md) |

### Images (1400 × 800, JPEG)

| Image | Caption | Raw URL |
|---|---|---|
| `docs/img/1-groups-top.jpg` | Groups: 2025, 609 groups, 248.8 Mt CO₂e attributed | https://raw.githubusercontent.com/Parsaka/belegt/main/docs/img/1-groups-top.jpg |
| `docs/img/2-reported-vs-verified-top.jpg` | Reported Scope 1 vs ETS sum per report, with page and quote | https://raw.githubusercontent.com/Parsaka/belegt/main/docs/img/2-reported-vs-verified-top.jpg |
| `docs/img/3-installations-top.jpg` | Installations map coloured by match decision | https://raw.githubusercontent.com/Parsaka/belegt/main/docs/img/3-installations-top.jpg |

The same images are served at `https://parsaka.github.io/belegt/img/<name>`.

## Rules for a page built from this repository

- **Use only measured numbers.** Use them as they appear here or in `docs/measurements/`, and
  link the source where possible. Do not round them differently or add new ones.
- **Attribute the data.** EU ETS Union Registry (© European Union), GLEIF (CC0), EEA Industrial
  Reporting (CC BY 4.0, © EEA), GeoNames (CC BY 4.0). Company reports are only linked and quoted,
  never re-hosted.
- **State what the project is.** It is a personal portfolio project, not investment, audit or
  legal advice.
- **Name GKE as temporary.** GKE runs only during the Google Cloud trial, and the report job
  moves to Cloud Run afterwards. Say so if the page shows GKE as part of the stack.
