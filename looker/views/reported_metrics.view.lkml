view: reported_metrics {
  sql_table_name: `marts.fct_reported_metric` ;;

  dimension: pk {
    primary_key: yes
    hidden: yes
    sql: CONCAT(${TABLE}.doc_id, '-', ${TABLE}.metric) ;;
  }
  dimension: doc_id { hidden: yes sql: ${TABLE}.doc_id ;; }
  dimension: metric {
    description: "scope1, scope2_market, scope2_location or scope3 (ESRS E1-6)."
    sql: ${TABLE}.metric ;;
  }
  dimension: page {
    type: number
    sql: ${TABLE}.page ;;
    link: {
      label: "Open the page in the report"
      url: "{{ url._value }}#page={{ value }}"
    }
  }
  dimension: url { hidden: yes sql: ${TABLE}.url ;; }
  dimension: unit_raw { label: "Unit as printed" sql: ${TABLE}.unit_raw ;; }
  dimension: quote { label: "Table line" sql: ${TABLE}.quote ;; }
  dimension: figure_source {
    description: "reviewed (a person checked the page) or extracted."
    sql: ${TABLE}.figure_source ;;
  }
  dimension: column_year {
    description: "The header year of the figure's column; empty when the table had no reporting-year column."
    type: number
    value_format_name: id
    sql: ${TABLE}.column_year ;;
  }

  measure: value_mt {
    label: "Reported (Mt CO2e)"
    type: sum
    sql: ${TABLE}.value_t / 1e6 ;;
    value_format_name: decimal_2
  }
}
