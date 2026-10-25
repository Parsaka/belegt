# Full German data: measured on 2026-10-25

Pipeline run [40234841717](https://github.com/Parsaka/belegt/actions/runs/40234841717) on GitHub
Actions: `belegt extract`, then `belegt load` and `dbt build` on DuckDB over the full files. The
same numbers come from BigQuery once the cloud job runs (`ops-results` branch, `runs/pipeline/`).

## Input files

| File | Rows | Size |
|---|---|---|
| EU ETS verified emissions (Union Registry, 2025 release) | 43,272 German account-years | 8.2 MB |
| EU ETS operator list | 2,874 German operators | 1.8 MB |
| EEA Industrial Reporting v16, German ETS links | 573 links, 146 installations, 43 facilities | |
| GLEIF golden copy, German entities plus every group parent | 310,087 entities | 40.4 MB |
| GLEIF golden copy, consolidation edges of those entities | 33,902 edges | 13.6 MB |

`belegt load` (parse, entity resolution for 1,538 distinct names, write) took 5 min 49 s on a
standard GitHub runner. `dbt build`: all 41 nodes (models, snapshot, seeds, tests) passed.

## Who emits: accounts matched to a company

| Kind | Accounts | Matched to a GLEIF company |
|---|---|---|
| Stationary installations | 2,195 | 1,697 (77.3 %) |
| Aircraft operators | 209 | 57 (27.3 %) |

Match decisions over all 2,404 accounts: 1,754 accepted, 126 in the review queue
(`review_entity_matches`, 113 distinct names), 425 unmatched, 99 without any candidate. Every
accepted match came from the registry's own account holder (register number or LEI first,
then the name); the EEA parent-company path adds nothing in this release, because the EEA links
only Brandenburg installations.

## How much of the tonnage is attributed

| Year | Verified t CO₂e | Attributed to a company | Share |
|---|---|---|---|
| 2025 | 271,463,310 | 248,798,685 | 91.7 % |
| 2024 | 281,883,555 | 258,716,042 | 91.8 % |
| 2023 | 296,983,646 | 273,341,057 | 92.0 % |

## Largest groups, 2025

Roll-up through GLEIF ultimate parents valid at the end of the year (`mart_group_emissions`).

| Group | Verified t CO₂e | Accounts |
|---|---|---|
| Lausitz Energie Kraftwerke AG (LEAG) | 38,826,938 | 7 |
| RWE Aktiengesellschaft | 36,008,223 | 14 |
| thyssenkrupp AG | 14,839,049 | 16 |
| Salzgitter Aktiengesellschaft | 7,297,456 | 11 |
| EnBW Energie Baden-Württemberg AG | 6,852,108 | 14 |
| Hüttenwerke Krupp Mannesmann GmbH | 6,499,927 | 3 |
| UNIPER SE | 5,613,342 | 22 |
| BASF SE | 5,085,396 | 47 |

Hüttenwerke Krupp Mannesmann has several shareholders (thyssenkrupp, Salzgitter, Vallourec) and
no consolidating parent in GLEIF, so it stays its own group. Attributing it pro rata would need
ownership shares, which GLEIF Level 2 does not carry.
