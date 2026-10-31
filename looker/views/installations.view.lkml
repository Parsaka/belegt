view: installations {
  sql_table_name: `marts.dim_installation` ;;

  dimension: ets_identifier {
    primary_key: yes
    description: "Registry code plus the 15-digit installation id, e.g. DE000000000001231."
    sql: ${TABLE}.ets_identifier ;;
  }
  dimension: installation_name { sql: ${TABLE}.installation_name ;; }
  dimension: account_holder { sql: ${TABLE}.account_holder ;; }
  dimension: installation_kind {
    description: "Stationary installation, aircraft operator or maritime operator."
    sql: ${TABLE}.installation_kind ;;
  }
  dimension: activity_code { type: number sql: ${TABLE}.activity_code ;; }
  dimension: city { sql: ${TABLE}.city ;; }
  dimension: state {
    description: "Bundesland of the postcode (GeoNames)."
    sql: ${TABLE}.state ;;
  }
  dimension: location_source {
    description: "EEA facility point, or the centre of the registry contact postcode."
    sql: ${TABLE}.location_source ;;
  }
  dimension: location {
    type: location
    sql_latitude: ${TABLE}.lat ;;
    sql_longitude: ${TABLE}.lon ;;
  }
  dimension: operator_lei { sql: ${TABLE}.operator_lei ;; }
  dimension: match_decision {
    description: "accepted, review, unmatched or rejected (entity resolution to GLEIF)."
    sql: ${TABLE}.match_decision ;;
  }
  dimension: match_path {
    description: "How the operator was matched: register number, LEI in the registry, or name."
    sql: ${TABLE}.match_path ;;
  }
  dimension: match_score { type: number sql: ${TABLE}.match_score ;; value_format_name: decimal_2 }

  measure: count { type: count drill_fields: [ets_identifier, installation_name, account_holder, match_decision] }
  measure: matched {
    type: count
    filters: [match_decision: "accepted"]
  }
  measure: match_rate {
    description: "Share of installations whose operator is matched to a GLEIF legal entity."
    type: number
    sql: ${matched} / NULLIF(${count}, 0) ;;
    value_format_name: percent_1
  }
}
