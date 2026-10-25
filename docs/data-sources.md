# Data sources

Checked on 2026-10-25 on each publisher's own page. Every source here must also be registered
in `src/belegt/sources.py`; a test enforces that. Column-level structure is confirmed in the
first ingestion step, by opening the files.

| id | Dataset | Where | Licence | Status |
|---|---|---|---|---|
| `eu_ets_union_registry` | EU ETS verified emissions and compliance data, yearly xlsx files (phase III 2013–2020, phase IV 2021–2025; the 2025 verified emissions were published 9 Apr 2026) | [Union Registry page](https://climate.ec.europa.eu/areas-action/carbon-markets/eu-emissions-trading-system-eu-ets/union-registry_en), plus the public site [union-registry-data.ec.europa.eu](https://union-registry-data.ec.europa.eu/) | No licence on the page. Commission reuse policy (Decision 2011/833/EU) allows reuse with attribution. | Partial: confirm installation-level granularity |
| `eea_industrial_reporting` | Industrial Reporting under the IED and E-PRTR, v13 (Dec 2024) or later. Facility releases 2007–2023. Includes an `ETSIdentifiers` table (installation ↔ EU ETS id) and the facility's parent company name. | [EEA SDI catalogue](https://sdi.eea.europa.eu/catalogue/srv/api/records/ff47e25d-5d4c-491d-b9ce-de17ca61fe6d) | CC BY 4.0, © EEA | Verified |
| `gleif_golden_copy` | LEI records (Level 1), direct and ultimate parents (Level 2 RR), reporting exceptions. Published three times a day, with deltas. | [GLEIF Golden Copy](https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy), [terms](https://www.gleif.org/en/meta/lei-data-terms-of-use) | CC0. Do not claim rights in the data or imply GLEIF endorsement. | Verified |
| `esrs_eurlex` | ESRS, Commission Delegated Regulation (EU) 2023/2772 | [EUR-Lex](https://eur-lex.europa.eu/eli/reg_del/2023/2772/oj) | EU legal text, reuse with attribution | Verified |
| `sustainability_statements` | Sustainability statements in the 2024 and 2025 annual reports of about 40 DAX/MDAX companies | Company investor-relations sites. Links are found through the [Sustainability Reporting Navigator](https://www.srnav.com/), which lists 500+ CSRD reports including DAX 40 (free registration). | Copyrighted. PDFs are stored privately only; Git holds links and metadata. | Unverified: SRN terms |

## Considered and not used

- **EEA EU ETS dataset** ([Sep 2026 release](https://www.eea.europa.eu/data-and-maps/data/european-union-emissions-trading-scheme-17)):
  aggregated by country and sector, not by installation. It is used only as a reconciliation
  check on totals.
- **filings.xbrl.org**: its own about page says German ESEF filings cannot be reliably
  discovered, so coverage would be partial.
- **EUI ownership links** ([EUI Research Data](https://cadmus.eui.eu/handle/1814/64596)):
  CC BY 4.0, but it covers only 2005–2007. It could serve as a sanity check for the matching
  method, not as a source.

## Known gaps

- EEA facility data lags EU ETS by one to two years, so pollutant comparisons stop earlier than
  CO₂ comparisons.
- The EU ETS covers only large installations in the EEA, so a group's reported Scope 1 is
  normally larger than the sum of its ETS installations. Only an ETS sum *above* reported Scope 1
  is a hard inconsistency.
