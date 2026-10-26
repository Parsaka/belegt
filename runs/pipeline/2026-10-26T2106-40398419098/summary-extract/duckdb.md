# Pipeline summary (duckdb)

## dbt build

58 nodes, 0 not passing, 0 bytes processed in total

All nodes passed.

<details><summary>All nodes</summary>

| node | status | seconds | bytes processed |
|---|---|---|---|
| stg_ets__emissions | success | 0.1 |  |
| stg_eea__installations | success | 0.1 |  |
| stg_ets__operators | success | 0.1 |  |
| stg_gleif__entities | success | 0.1 |  |
| entity_overrides | success | 0.1 |  |
| reported_overrides | success | 0.1 |  |
| stg_reported_metrics | success | 0.1 |  |
| stg_gleif__relationships | success | 0.1 |  |
| reports | success | 0.1 |  |
| not_null_stg_ets__operators_ets_identifier.c920d77abe | pass | 0.1 |  |
| not_null_stg_eea__installations_ets_identifier.5564ead76b | pass | 0.2 |  |
| unique_stg_eea__installations_ets_identifier.fa6a29f48f | pass | 0.1 |  |
| fct_verified_emissions | success | 0.2 |  |
| unique_stg_ets__operators_ets_identifier.61e4f719d5 | pass | 0.1 |  |
| not_null_stg_gleif__entities_lei.ff170eff45 | pass | 0.1 |  |
| unique_stg_gleif__entities_lei.bf0166410b | pass | 0.1 |  |
| accepted_values_entity_overrides_decision__accepted__rejected.73b827b271 | pass | 0.1 |  |
| not_null_entity_overrides_source_name.6b66b9b108 | pass | 0.1 |  |
| unique_entity_overrides_source_name.68557629d6 | pass | 0.1 |  |
| unique_combination_reported_overrides_doc_id__metric.013526b6a9 | pass | 0.1 |  |
| unique_reports_doc_id.f06c97810a | pass | 0.0 |  |
| not_null_reports_doc_id.64e9792ddf | pass | 0.1 |  |
| not_null_reports_lei.63c7db607a | pass | 0.1 |  |
| non_negative_fct_verified_emissions_verified_t.6ad4fd252e | pass | 0.1 |  |
| not_null_fct_verified_emissions_ets_identifier.e7689127db | pass | 0.0 |  |
| unique_combination_fct_verified_emissions_ets_identifier__reporting_year.88360e7859 | pass | 0.1 |  |
| stg_entity_matches | success | 0.1 |  |
| fct_reported_metric | success | 0.1 |  |
| not_null_stg_entity_matches_source_name.8f2f9d47f2 | pass | 0.0 |  |
| accepted_values_stg_entity_matches_decision__accepted__review__unmatched__rejected.1b61b004de | pass | 0.0 |  |
| unique_stg_entity_matches_source_name.e97db9fdf9 | pass | 0.0 |  |
| accepted_values_fct_reported_metric_metric__scope1__scope2_market__scope2_location__scope3.b44a420927 | pass | 0.0 |  |
| non_negative_fct_reported_metric_value_t.3b79ff9422 | pass | 0.0 |  |
| not_null_fct_reported_metric_page.4408e208c6 | pass | 0.0 |  |
| bridge_ownership | success | 0.3 |  |
| unique_combination_fct_reported_metric_doc_id__metric.9f1faa5820 | pass | 0.1 |  |
| int_installation_entity | success | 0.1 |  |
| accepted_values_bridge_ownership_relationship_kind__direct__ultimate__self.026fbe75b2 | pass | 0.1 |  |
| review_entity_matches | success | 0.1 |  |
| dim_installation | success | 0.1 |  |
| no_overlapping_periods_bridge_ownership_.0d075ddcd4 | pass | 0.1 |  |
| accepted_values_dim_installation_match_decision__accepted__review__unmatched__rejected.f7d06bb854 | pass | 0.0 |  |
| not_null_dim_installation_ets_identifier.3f8cb366d2 | pass | 0.0 |  |
| accepted_values_dim_installation_installation_kind__stationary_installation__aircraft_operator__maritime_operator.fa4177d252 | pass | 0.1 |  |
| relationships_fct_verified_emissions_ets_identifier__ets_identifier__ref_dim_installation_.82e871d770 | pass | 0.0 |  |
| unique_dim_installation_ets_identifier.9d9f615ed8 | pass | 0.0 |  |
| mart_group_emissions | success | 0.1 |  |
| unique_combination_mart_group_emissions_group_lei__reporting_year.4b7f556066 | pass | 0.0 |  |
| group_total_matches_attributed_facts_mart_group_emissions_.6874f739d0 | pass | 0.0 |  |
| mart_scope1_consistency | success | 0.0 |  |
| unique_mart_scope1_consistency_doc_id.6572c5dc33 | pass | 0.0 |  |
| accepted_values_mart_scope1_consistency_status__consistent__ets_exceeds_reported__no_reported_figure__no_ets_group.19c6fea9f5 | pass | 0.0 |  |
| not_null_mart_scope1_consistency_doc_id.288af9e417 | pass | 0.1 |  |
| snap_gleif_entities | success | 0.9 |  |
| dim_legal_entity | success | 0.4 |  |
| not_null_dim_legal_entity_legal_entity_key.53c0fc4098 | pass | 0.1 |  |
| one_current_version_per_lei_dim_legal_entity_.52f16d8757 | pass | 0.1 |  |
| unique_dim_legal_entity_legal_entity_key.9c8c406d43 | pass | 0.1 |  |

</details>

## Rows per mart

| model | rows |
|---|---|
| dim_installation | 2404 |
| fct_verified_emissions | 43,272 |
| dim_legal_entity | 310,168 |
| bridge_ownership | 344,064 |
| mart_group_emissions | 11,969 |
| review_entity_matches | 113 |

## Accounts by kind

| kind | accounts | matched to a company |
|---|---|---|
| stationary installation | 2195 | 1697 |
| aircraft operator | 209 | 57 |

## Installations by match decision and path

| decision | path | installations |
|---|---|---|
| accepted | registry account holder | 1754 |
| unmatched | registry account holder | 425 |
| review | registry account holder | 126 |
| no candidate | None | 99 |

## Verified tonnes attributed to a company, by year (last five)

| year | verified t | attributed t |
|---|---|---|
| 2025 | 271,463,310 | 248,798,685 |
| 2024 | 281,883,555 | 258,716,042 |
| 2023 | 296,983,646 | 273,341,057 |
| 2022 | 361,145,578 | 333,700,704 |
| 2021 | 359,774,844 | 330,947,195 |

## Largest groups in the latest year

| group | LEI | year | verified t | installations |
|---|---|---|---|---|
| Lausitz Energie Kraftwerke AG | 391200AHHWMFQOVPBZ32 | 2025 | 38,826,938 | 7 |
| RWE Aktiengesellschaft | 529900GB7KCA94ACC940 | 2025 | 36,008,223 | 14 |
| thyssenkrupp AG | 549300UDG16DOYUPR330 | 2025 | 14,839,049 | 16 |
| Salzgitter Aktiengesellschaft | 529900E12Z6HXIMHFA15 | 2025 | 7,297,456 | 11 |
| EnBW Energie Baden-Württemberg AG | 529900JSFZ4TS59HKD79 | 2025 | 6,852,108 | 14 |
| Hüttenwerke Krupp Mannesmann Gesellschaft mit beschränkter Haftung | 52990047WY6J8GKPEI91 | 2025 | 6,499,927 | 3 |
| UNIPER SE | 549300UXRTWGIBZQ4J67 | 2025 | 5,613,342 | 22 |
| BASF SE | 529900PM64WH8AF1E917 | 2025 | 5,085,396 | 47 |
| ArcelorMittal Bremen GmbH | 5493000C5WM5LHZWSB48 | 2025 | 4,906,120 | 7 |
| Saale Energie GmbH | 529900EFRY9L8JC9CQ37 | 2025 | 3,958,812 | 1 |
| Ruhr Oel GmbH | 391200T3F0IW81QXXQ03 | 2025 | 3,936,488 | 2 |
| Grosskraftwerk Mannheim Aktiengesellschaft | 529900F4P4RV4Z50PI82 | 2025 | 3,773,541 | 1 |
| PCK Raffinerie GmbH | 529900WWXYN48AOXBA25 | 2025 | 3,317,233 | 1 |
| Deutsche Lufthansa Aktiengesellschaft | 529900PH63HYJ86ASW55 | 2025 | 3,297,247 | 6 |
| Heidelberg Materials AG | LZ2C6E0W5W7LQMX5ZI37 | 2025 | 2,871,849 | 7 |
