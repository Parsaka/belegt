# Fixtures

Trimmed real rows, built by `scripts/build_fixtures.py` in GitHub Actions on 2026-10-25.
Nothing here is invented; the only change is fewer rows and, for GLEIF, fewer JSON fields.

| File | Source | Rows kept |
|---|---|---|
| `ets_verified_emissions_de.xlsx` | Union Registry, `verified_emissions_2025_en.xlsx` (sheet `data`, with its preamble rows) | every German installation the EEA links, group sites, an even spread of the rest |
| `ets_operators_de.xlsx` | Union Registry, `policy_ets_registry_operators_ets_en.xlsx` | the operators of those installations |
| `eea_*.csv` | EEA Industrial Reporting v16 Access database (`mdb-export`) | the ETS-id, installation and facility rows of those installations |
| `gleif_entities_*.json` | GLEIF API (CC0) | records found by operator LEI, register number and name, plus the group members |
| `gleif_rr.csv` | GLEIF golden copy RR file of 2026-10-25 (CC0) | every relationship touching BASF SE, Heidelberg Materials AG or RWE AG |
