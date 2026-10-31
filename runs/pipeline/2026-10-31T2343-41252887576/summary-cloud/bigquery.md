# Pipeline summary (bigquery)

## dbt build

65 nodes, 50 not passing, 0 bytes processed in total

| node | status | seconds | bytes processed |
|---|---|---|---|
| not_null_stg_gleif__entities_lei.ff170eff45 | error | 0.8 |  |
| unique_stg_gleif__entities_lei.bf0166410b | error | 0.9 |  |
| not_null_stg_ets__operators_ets_identifier.c920d77abe | error | 0.7 |  |
| unique_stg_ets__operators_ets_identifier.61e4f719d5 | error | 0.7 |  |
| not_null_stg_eea__installations_ets_identifier.5564ead76b | error | 0.7 |  |
| unique_stg_eea__installations_ets_identifier.fa6a29f48f | error | 0.7 |  |
| fct_verified_emissions | error | 1.2 |  |
| bridge_ownership | skipped | 0 |  |
| snap_gleif_entities | skipped | 0 |  |
| non_negative_fct_verified_emissions_verified_t.6ad4fd252e | skipped | 0 |  |
| not_null_fct_verified_emissions_ets_identifier.e7689127db | skipped | 0 |  |
| unique_combination_fct_verified_emissions_ets_identifier__reporting_year.88360e7859 | skipped | 0 |  |
| not_null_states_state_code.4c83882290 | error | 0.5 |  |
| not_null_reports_doc_id.64e9792ddf | error | 0.4 |  |
| not_null_reports_lei.63c7db607a | error | 0.4 |  |
| accepted_values_bridge_ownership_relationship_kind__direct__ultimate__self.026fbe75b2 | skipped | 0 |  |
| no_overlapping_periods_bridge_ownership_.0d075ddcd4 | skipped | 0 |  |
| dim_legal_entity | skipped | 0 |  |
| unique_states_state_code.67c4706beb | error | 0.5 |  |
| not_null_dim_legal_entity_legal_entity_key.53c0fc4098 | skipped | 0 |  |
| one_current_version_per_lei_dim_legal_entity_.52f16d8757 | skipped | 0 |  |
| unique_dim_legal_entity_legal_entity_key.9c8c406d43 | skipped | 0 |  |
| stg_geonames__postcodes | skipped | 0 |  |
| unique_stg_geonames__postcodes_postcode.1d63c4347e | skipped | 0 |  |
| not_null_stg_geonames__postcodes_postcode.acba7b1d2d | skipped | 0 |  |
| unique_reports_doc_id.f06c97810a | error | 0.4 |  |
| fct_reported_metric | skipped | 0 |  |
| accepted_values_fct_reported_metric_metric__scope1__scope2_market__scope2_location__scope3.b44a420927 | skipped | 0 |  |
| non_negative_fct_reported_metric_value_t.3b79ff9422 | skipped | 0 |  |
| not_null_fct_reported_metric_page.4408e208c6 | skipped | 0 |  |
| unique_combination_fct_reported_metric_doc_id__metric.9f1faa5820 | skipped | 0 |  |
| accepted_values_stg_entity_matches_decision__accepted__review__unmatched__rejected.1b61b004de | error | 0.7 |  |
| unique_stg_entity_matches_source_name.e97db9fdf9 | error | 0.8 |  |
| not_null_stg_entity_matches_source_name.8f2f9d47f2 | error | 0.8 |  |
| int_installation_entity | skipped | 0 |  |
| review_entity_matches | skipped | 0 |  |
| dim_installation | skipped | 0 |  |
| accepted_values_dim_installation_installation_kind__stationary_installation__aircraft_operator__maritime_operator.fa4177d252 | skipped | 0 |  |
| accepted_values_dim_installation_location_source__EEA_facility__contact_postcode.45fb075a8d | skipped | 0 |  |
| accepted_values_dim_installation_match_decision__accepted__review__unmatched__rejected.f7d06bb854 | skipped | 0 |  |
| not_null_dim_installation_ets_identifier.3f8cb366d2 | skipped | 0 |  |
| relationships_fct_verified_emissions_ets_identifier__ets_identifier__ref_dim_installation_.82e871d770 | skipped | 0 |  |
| unique_dim_installation_ets_identifier.9d9f615ed8 | skipped | 0 |  |
| mart_group_emissions | skipped | 0 |  |
| group_total_matches_attributed_facts_mart_group_emissions_.6874f739d0 | skipped | 0 |  |
| unique_combination_mart_group_emissions_group_lei__reporting_year.4b7f556066 | skipped | 0 |  |
| mart_scope1_consistency | skipped | 0 |  |
| accepted_values_mart_scope1_consistency_status__consistent__ets_exceeds_reported__no_reported_figure__no_ets_group.19c6fea9f5 | skipped | 0 |  |
| not_null_mart_scope1_consistency_doc_id.288af9e417 | skipped | 0 |  |
| unique_mart_scope1_consistency_doc_id.6572c5dc33 | skipped | 0 |  |

<details><summary>All nodes</summary>

| node | status | seconds | bytes processed |
|---|---|---|---|
| stg_gleif__entities | success | 1.0 | 0 |
| stg_ets__operators | success | 1.0 | 0 |
| stg_eea__installations | success | 1.0 | 0 |
| stg_ets__emissions | success | 1.0 | 0 |
| stg_reported_metrics | success | 0.9 | 0 |
| stg_gleif__relationships | success | 0.9 | 0 |
| entity_overrides | success | 1.8 |  |
| reported_overrides | success | 1.7 |  |
| not_null_stg_gleif__entities_lei.ff170eff45 | error | 0.8 |  |
| unique_stg_gleif__entities_lei.bf0166410b | error | 0.9 |  |
| not_null_stg_ets__operators_ets_identifier.c920d77abe | error | 0.7 |  |
| unique_stg_ets__operators_ets_identifier.61e4f719d5 | error | 0.7 |  |
| not_null_stg_eea__installations_ets_identifier.5564ead76b | error | 0.7 |  |
| unique_stg_eea__installations_ets_identifier.fa6a29f48f | error | 0.7 |  |
| accepted_values_entity_overrides_decision__accepted__rejected.73b827b271 | pass | 1.1 | 0 |
| fct_verified_emissions | error | 1.2 |  |
| states | success | 4.7 |  |
| reports | success | 4.9 |  |
| bridge_ownership | skipped | 0 |  |
| snap_gleif_entities | skipped | 0 |  |
| non_negative_fct_verified_emissions_verified_t.6ad4fd252e | skipped | 0 |  |
| not_null_fct_verified_emissions_ets_identifier.e7689127db | skipped | 0 |  |
| unique_combination_fct_verified_emissions_ets_identifier__reporting_year.88360e7859 | skipped | 0 |  |
| unique_entity_overrides_source_name.68557629d6 | pass | 1.1 | 0 |
| not_null_entity_overrides_source_name.6b66b9b108 | pass | 1.1 | 0 |
| not_null_states_state_code.4c83882290 | error | 0.5 |  |
| not_null_reports_doc_id.64e9792ddf | error | 0.4 |  |
| not_null_reports_lei.63c7db607a | error | 0.4 |  |
| accepted_values_bridge_ownership_relationship_kind__direct__ultimate__self.026fbe75b2 | skipped | 0 |  |
| no_overlapping_periods_bridge_ownership_.0d075ddcd4 | skipped | 0 |  |
| dim_legal_entity | skipped | 0 |  |
| unique_combination_reported_overrides_doc_id__metric.013526b6a9 | pass | 1.2 | 0 |
| unique_states_state_code.67c4706beb | error | 0.5 |  |
| not_null_dim_legal_entity_legal_entity_key.53c0fc4098 | skipped | 0 |  |
| one_current_version_per_lei_dim_legal_entity_.52f16d8757 | skipped | 0 |  |
| unique_dim_legal_entity_legal_entity_key.9c8c406d43 | skipped | 0 |  |
| stg_geonames__postcodes | skipped | 0 |  |
| unique_stg_geonames__postcodes_postcode.1d63c4347e | skipped | 0 |  |
| not_null_stg_geonames__postcodes_postcode.acba7b1d2d | skipped | 0 |  |
| unique_reports_doc_id.f06c97810a | error | 0.4 |  |
| fct_reported_metric | skipped | 0 |  |
| accepted_values_fct_reported_metric_metric__scope1__scope2_market__scope2_location__scope3.b44a420927 | skipped | 0 |  |
| non_negative_fct_reported_metric_value_t.3b79ff9422 | skipped | 0 |  |
| not_null_fct_reported_metric_page.4408e208c6 | skipped | 0 |  |
| unique_combination_fct_reported_metric_doc_id__metric.9f1faa5820 | skipped | 0 |  |
| stg_entity_matches | success | 0.9 | 0 |
| accepted_values_stg_entity_matches_decision__accepted__review__unmatched__rejected.1b61b004de | error | 0.7 |  |
| unique_stg_entity_matches_source_name.e97db9fdf9 | error | 0.8 |  |
| not_null_stg_entity_matches_source_name.8f2f9d47f2 | error | 0.8 |  |
| int_installation_entity | skipped | 0 |  |
| review_entity_matches | skipped | 0 |  |
| dim_installation | skipped | 0 |  |
| accepted_values_dim_installation_installation_kind__stationary_installation__aircraft_operator__maritime_operator.fa4177d252 | skipped | 0 |  |
| accepted_values_dim_installation_location_source__EEA_facility__contact_postcode.45fb075a8d | skipped | 0 |  |
| accepted_values_dim_installation_match_decision__accepted__review__unmatched__rejected.f7d06bb854 | skipped | 0 |  |
| not_null_dim_installation_ets_identifier.3f8cb366d2 | skipped | 0 |  |
| relationships_fct_verified_emissions_ets_identifier__ets_identifier__ref_dim_installation_.82e871d770 | skipped | 0 |  |
| unique_dim_installation_ets_identifier.9d9f615ed8 | skipped | 0 |  |
| mart_group_emissions | skipped | 0 |  |
| group_total_matches_attributed_facts_mart_group_emissions_.6874f739d0 | skipped | 0 |  |
| unique_combination_mart_group_emissions_group_lei__reporting_year.4b7f556066 | skipped | 0 |  |
| mart_scope1_consistency | skipped | 0 |  |
| accepted_values_mart_scope1_consistency_status__consistent__ets_exceeds_reported__no_reported_figure__no_ets_group.19c6fea9f5 | skipped | 0 |  |
| not_null_mart_scope1_consistency_doc_id.288af9e417 | skipped | 0 |  |
| unique_mart_scope1_consistency_doc_id.6572c5dc33 | skipped | 0 |  |

</details>

## Rows per mart

| model | rows |
|---|---|
| dim_installation | 2404 |
| fct_verified_emissions | 43,272 |
| dim_legal_entity | 317,687 |
| bridge_ownership | 344,517 |
| mart_group_emissions | 11,969 |
| review_entity_matches | 112 |

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

## Installations with a map point, by source

| source | stationary installations |
|---|---|
| contact postcode | 2015 |
| no point | 131 |
| EEA facility | 49 |

## Verified tonnes attributed to a company, by year (last five)

_query failed: 403 Custom quota exceeded: Your usage exceeded the custom quota for QueryUsagePerDay, which is set by your administrator. For more information, see https://docs.cloud.google.com/bigquery/cost-controls. To update the limit, go to https://docs.cloud.google.com/bigquery/redirects/increase-query-cost-quota.; reason: quotaExceeded, message: Custom quota exceeded: Your usage exceeded the custom quota for QueryUsagePerDay, which is set by your administrator. For more information, see https://docs.cloud.google.com/bigquery/cost-controls. To update the limit, go to https://docs.cloud.google.com/bigquery/redirects/increase-query-cost-quota.

Location: EU
Job ID: 6dca7db8-dfe5-46ad-8b1c-171ddec08245
_

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
