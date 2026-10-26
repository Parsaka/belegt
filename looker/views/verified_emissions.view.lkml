view: verified_emissions {
  sql_table_name: `marts.fct_verified_emissions` ;;

  dimension: pk {
    primary_key: yes
    hidden: yes
    sql: CONCAT(${TABLE}.ets_identifier, '-', CAST(${TABLE}.reporting_year AS STRING)) ;;
  }
  dimension: ets_identifier { hidden: yes sql: ${TABLE}.ets_identifier ;; }
  dimension: reporting_year { type: number value_format_name: id sql: ${TABLE}.reporting_year ;; }
  dimension: status {
    description: "Compliance status in the registry; 'n/a' years have no verified figure (null, not 0)."
    sql: ${TABLE}.status ;;
  }
  dimension: is_reported { type: yesno sql: ${TABLE}.is_reported ;; }

  measure: verified_t {
    label: "Verified emissions (t CO2e)"
    type: sum
    sql: ${TABLE}.verified_t ;;
    value_format_name: decimal_0
  }
  measure: verified_mt {
    label: "Verified emissions (Mt CO2e)"
    type: sum
    sql: ${TABLE}.verified_t / 1e6 ;;
    value_format_name: decimal_2
  }
  measure: allocation_t {
    label: "Free allocation (t)"
    type: sum
    sql: ${TABLE}.allocation_t ;;
    value_format_name: decimal_0
  }
}
