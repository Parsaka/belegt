view: group_emissions {
  sql_table_name: `marts.mart_group_emissions` ;;

  dimension: pk {
    primary_key: yes
    hidden: yes
    sql: CONCAT(${TABLE}.group_lei, '-', CAST(${TABLE}.reporting_year AS STRING)) ;;
  }
  dimension: group_lei { label: "Group LEI" sql: ${TABLE}.group_lei ;; }
  dimension: group_name {
    sql: ${TABLE}.group_name ;;
    link: {
      label: "GLEIF record"
      url: "https://search.gleif.org/#/record/{{ group_lei._value }}"
    }
  }
  dimension: reporting_year { type: number value_format_name: id sql: ${TABLE}.reporting_year ;; }

  measure: verified_mt {
    label: "Verified emissions (Mt CO2e)"
    type: sum
    sql: ${TABLE}.verified_t / 1e6 ;;
    value_format_name: decimal_2
  }
  measure: installations { type: sum sql: ${TABLE}.installations ;; }
}
