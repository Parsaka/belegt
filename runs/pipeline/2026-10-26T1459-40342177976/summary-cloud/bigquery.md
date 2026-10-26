# Pipeline summary (bigquery)

## dbt build

58 nodes, 34 not passing, 155,135,468 bytes processed in total

| node | status | seconds | bytes processed |
|---|---|---|---|
| entity_overrides | error | 0.7 |  |
| reported_overrides | error | 0.8 |  |
| reports | error | 0.3 |  |
| accepted_values_entity_overrides_decision__accepted__rejected.73b827b271 | skipped | 0 |  |
| not_null_entity_overrides_source_name.6b66b9b108 | skipped | 0 |  |
| unique_entity_overrides_source_name.68557629d6 | skipped | 0 |  |
| unique_combination_reported_overrides_doc_id__metric.013526b6a9 | skipped | 0 |  |
| not_null_reports_doc_id.64e9792ddf | skipped | 0 |  |
| not_null_reports_lei.63c7db607a | skipped | 0 |  |
| unique_reports_doc_id.f06c97810a | skipped | 0 |  |
| stg_entity_matches | skipped | 0 |  |
| fct_reported_metric | skipped | 0 |  |
| accepted_values_stg_entity_matches_decision__accepted__review__unmatched__rejected.1b61b004de | skipped | 0 |  |
| not_null_stg_entity_matches_source_name.8f2f9d47f2 | skipped | 0 |  |
| unique_stg_entity_matches_source_name.e97db9fdf9 | skipped | 0 |  |
| accepted_values_fct_reported_metric_metric__scope1__scope2_market__scope2_location__scope3.b44a420927 | skipped | 0 |  |
| non_negative_fct_reported_metric_value_t.3b79ff9422 | skipped | 0 |  |
| not_null_fct_reported_metric_page.4408e208c6 | skipped | 0 |  |
| unique_combination_fct_reported_metric_doc_id__metric.9f1faa5820 | skipped | 0 |  |
| int_installation_entity | skipped | 0 |  |
| review_entity_matches | skipped | 0 |  |
| dim_installation | skipped | 0 |  |
| accepted_values_dim_installation_installation_kind__stationary_installation__aircraft_operator__maritime_operator.fa4177d252 | skipped | 0 |  |
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
| stg_eea__installations | success | 1.4 | 0 |
| stg_ets__emissions | success | 1.5 | 0 |
| stg_gleif__entities | success | 1.6 | 0 |
| stg_ets__operators | success | 1.6 | 0 |
| entity_overrides | error | 0.7 |  |
| reported_overrides | error | 0.8 |  |
| stg_reported_metrics | success | 1.1 | 0 |
| reports | error | 0.3 |  |
| stg_gleif__relationships | success | 1.2 | 0 |
| fct_verified_emissions | success | 2.7 | 1,691,869 |
| not_null_stg_eea__installations_ets_identifier.5564ead76b | pass | 6.2 | 79,010 |
| unique_stg_gleif__entities_lei.bf0166410b | pass | 3.3 | 6,822,112 |
| unique_stg_eea__installations_ets_identifier.fa6a29f48f | pass | 6.2 | 79,010 |
| accepted_values_entity_overrides_decision__accepted__rejected.73b827b271 | skipped | 0 |  |
| not_null_entity_overrides_source_name.6b66b9b108 | skipped | 0 |  |
| unique_entity_overrides_source_name.68557629d6 | skipped | 0 |  |
| unique_combination_reported_overrides_doc_id__metric.013526b6a9 | skipped | 0 |  |
| not_null_reports_doc_id.64e9792ddf | skipped | 0 |  |
| not_null_reports_lei.63c7db607a | skipped | 0 |  |
| unique_reports_doc_id.f06c97810a | skipped | 0 |  |
| not_null_stg_gleif__entities_lei.ff170eff45 | pass | 6.2 | 6,822,112 |
| not_null_fct_verified_emissions_ets_identifier.e7689127db | pass | 1.2 | 822,168 |
| non_negative_fct_verified_emissions_verified_t.6ad4fd252e | pass | 1.5 | 256,152 |
| stg_entity_matches | skipped | 0 |  |
| fct_reported_metric | skipped | 0 |  |
| unique_stg_ets__operators_ets_identifier.61e4f719d5 | pass | 2.0 | 29,367 |
| not_null_stg_ets__operators_ets_identifier.c920d77abe | pass | 2.0 | 29,367 |
| accepted_values_stg_entity_matches_decision__accepted__review__unmatched__rejected.1b61b004de | skipped | 0 |  |
| not_null_stg_entity_matches_source_name.8f2f9d47f2 | skipped | 0 |  |
| unique_stg_entity_matches_source_name.e97db9fdf9 | skipped | 0 |  |
| accepted_values_fct_reported_metric_metric__scope1__scope2_market__scope2_location__scope3.b44a420927 | skipped | 0 |  |
| non_negative_fct_reported_metric_value_t.3b79ff9422 | skipped | 0 |  |
| not_null_fct_reported_metric_page.4408e208c6 | skipped | 0 |  |
| unique_combination_fct_reported_metric_doc_id__metric.9f1faa5820 | skipped | 0 |  |
| int_installation_entity | skipped | 0 |  |
| review_entity_matches | skipped | 0 |  |
| dim_installation | skipped | 0 |  |
| accepted_values_dim_installation_installation_kind__stationary_installation__aircraft_operator__maritime_operator.fa4177d252 | skipped | 0 |  |
| accepted_values_dim_installation_match_decision__accepted__review__unmatched__rejected.f7d06bb854 | skipped | 0 |  |
| not_null_dim_installation_ets_identifier.3f8cb366d2 | skipped | 0 |  |
| relationships_fct_verified_emissions_ets_identifier__ets_identifier__ref_dim_installation_.82e871d770 | skipped | 0 |  |
| unique_dim_installation_ets_identifier.9d9f615ed8 | skipped | 0 |  |
| unique_combination_fct_verified_emissions_ets_identifier__reporting_year.88360e7859 | pass | 1.3 | 1,168,344 |
| bridge_ownership | success | 3.5 | 9,874,102 |
| accepted_values_bridge_ownership_relationship_kind__direct__ultimate__self.026fbe75b2 | pass | 1.4 | 2,166,480 |
| no_overlapping_periods_bridge_ownership_.0d075ddcd4 | pass | 1.4 | 22,806,360 |
| mart_group_emissions | skipped | 0 |  |
| group_total_matches_attributed_facts_mart_group_emissions_.6874f739d0 | skipped | 0 |  |
| unique_combination_mart_group_emissions_group_lei__reporting_year.4b7f556066 | skipped | 0 |  |
| mart_scope1_consistency | skipped | 0 |  |
| accepted_values_mart_scope1_consistency_status__consistent__ets_exceeds_reported__no_reported_figure__no_ets_group.19c6fea9f5 | skipped | 0 |  |
| not_null_mart_scope1_consistency_doc_id.288af9e417 | skipped | 0 |  |
| unique_mart_scope1_consistency_doc_id.6572c5dc33 | skipped | 0 |  |
| snap_gleif_entities | success | 5.2 | 43,036,605 |
| dim_legal_entity | success | 3.7 | 31,233,674 |
| unique_dim_legal_entity_legal_entity_key.9c8c406d43 | pass | 1.4 | 10,543,264 |
| not_null_dim_legal_entity_legal_entity_key.53c0fc4098 | pass | 1.4 | 10,543,264 |
| one_current_version_per_lei_dim_legal_entity_.52f16d8757 | pass | 1.6 | 7,132,208 |

</details>

## Rows per mart

_query failed: 404 Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU; reason: notFound, message: Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU

Location: EU
Job ID: 02276cc6-4beb-4b4c-8be4-625674c68c3d
_

## Accounts by kind

_query failed: 404 Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU; reason: notFound, message: Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU

Location: EU
Job ID: 65fa5e65-1368-4bbc-9584-9c616cc6c23e
_

## Installations by match decision and path

_query failed: 404 Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU; reason: notFound, message: Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU

Location: EU
Job ID: fb9c6107-bcb0-4bb1-baa7-08321bad1ccc
_

## Verified tonnes attributed to a company, by year (last five)

_query failed: 404 Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU; reason: notFound, message: Not found: Table belegt-pk-2610:marts.dim_installation was not found in location EU

Location: EU
Job ID: 9db7057f-7598-4641-af75-e1622458b2bb
_

## Largest groups in the latest year

_query failed: 404 Not found: Table belegt-pk-2610:marts.mart_group_emissions was not found in location EU; reason: notFound, message: Not found: Table belegt-pk-2610:marts.mart_group_emissions was not found in location EU

Location: EU
Job ID: 4f0e7314-79ca-403e-9bb6-27127e105761
_
