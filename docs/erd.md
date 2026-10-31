# Data model

The marts in BigQuery (`marts` dataset), as built by dbt. Column lists show the keys and the
columns the dashboard and the consistency check use; the full column docs are in the
[dbt docs](https://parsaka.github.io/belegt/).

```mermaid
erDiagram
    dim_installation ||--o{ fct_verified_emissions : "ets_identifier"
    dim_installation }o--o| dim_legal_entity : "operator_lei = lei (current version)"
    dim_legal_entity ||--o{ bridge_ownership : "lei = child_lei"
    dim_legal_entity ||--o{ bridge_ownership : "lei = parent_lei"
    bridge_ownership ||--o{ mart_group_emissions : "parent_lei = group_lei, valid in the year"
    reports ||--o{ fct_reported_metric : "doc_id"
    reports ||--|| mart_scope1_consistency : "doc_id"
    mart_group_emissions ||--o{ mart_scope1_consistency : "group_lei = lei, year"

    dim_installation {
        string ets_identifier PK "DE + 15-digit registry id"
        string installation_name
        string installation_kind "stationary, aircraft, maritime"
        string operator_lei FK "entity resolution result"
        string match_decision "accepted, review, unmatched, rejected"
        float match_score
        string match_path "registry LEI, register number, name, EEA parent"
        string state "Bundesland"
        float lat
        float lon
        string location_source "EEA facility or contact postcode"
    }
    fct_verified_emissions {
        string ets_identifier FK
        int reporting_year
        float verified_t "tonnes CO2e, null when not reported"
        float allocation_t
        string status
    }
    dim_legal_entity {
        string legal_entity_key PK "lei + valid_from"
        string lei
        string legal_name
        string registered_as "HRB number"
        timestamp valid_from "SCD2"
        timestamp valid_to "SCD2"
        bool is_current
    }
    bridge_ownership {
        string child_lei FK
        string parent_lei FK
        string relationship_kind "direct, ultimate, self"
        date valid_from
        date valid_to
    }
    mart_group_emissions {
        string group_lei PK
        int reporting_year PK
        string group_name
        float verified_t
        int installations
    }
    reports {
        string doc_id PK
        string company
        string lei
        int report_year
        string fiscal_year_end
        string url
    }
    fct_reported_metric {
        string doc_id FK
        string metric "scope1, scope2_location, scope2_market, scope3"
        float value_t
        int page "citation"
        string quote "table line, at most 200 chars"
        string figure_source "extracted or reviewed override"
    }
    mart_scope1_consistency {
        string doc_id PK
        float reported_scope1_t
        int reported_page
        float ets_verified_t
        float ets_share_of_reported
        string status "consistent, ets_exceeds_reported, ..."
    }
```

## Decisions worth knowing

- **SCD2 on GLEIF entities** (`snap_gleif_entities`): names, addresses and status change; a fact
  joins the version valid at its date.
- **Time-bounded ownership bridge:** "which group owned this plant *in 2022*" is a join on
  `valid_from`/`valid_to` at the year end, not on today's parent. Each entity also has a `self`
  edge, so an operator without a GLEIF parent is its own group.
- **Entity resolution with a review queue:** registry LEI first, then the commercial register
  number against GLEIF `registeredAs`, then the normalised name, then the EEA parent name.
  Uncertain matches go to `review_entity_matches`; human decisions are the seed
  `entity_overrides.csv`, so the matcher never changes silently.
- **Reported vs verified:** ETS covers only EU installations, so reported Scope 1 is normally
  *above* the ETS sum. Only ETS above reported (with a 5 % tolerance) is a hard inconsistency.
