view: scope1_consistency {
  sql_table_name: `marts.mart_scope1_consistency` ;;

  dimension: doc_id { primary_key: yes sql: ${TABLE}.doc_id ;; }
  dimension: company { sql: ${TABLE}.company ;; }
  dimension: lei { label: "LEI" sql: ${TABLE}.lei ;; }
  dimension: report_year { type: number value_format_name: id sql: ${TABLE}.report_year ;; }
  dimension: status {
    description: "ets_exceeds_reported: the German ETS installations alone emit more than the group reports worldwide (5 % tolerance)."
    sql: ${TABLE}.status ;;
    html:
      {% if value == 'ets_exceeds_reported' %}<span style="color:#b3261e;font-weight:600">{{ value }}</span>
      {% else %}{{ value }}{% endif %} ;;
  }
  dimension: caveat { sql: ${TABLE}.caveat ;; }
  dimension: reported_page { type: number sql: ${TABLE}.reported_page ;; }
  dimension: reported_quote {
    description: "The table line the figure was taken from (at most 200 characters)."
    sql: ${TABLE}.reported_quote ;;
  }
  dimension: ets_share_of_reported {
    description: "Verified ETS emissions (Germany) divided by reported Scope 1 (worldwide)."
    type: number
    sql: ${TABLE}.ets_share_of_reported ;;
    value_format_name: percent_1
  }

  measure: reported_scope1_mt {
    label: "Reported Scope 1 (Mt CO2e)"
    type: sum
    sql: ${TABLE}.reported_scope1_t / 1e6 ;;
    value_format_name: decimal_2
  }
  measure: ets_verified_mt {
    label: "Verified ETS, Germany (Mt CO2e)"
    type: sum
    sql: ${TABLE}.ets_verified_t / 1e6 ;;
    value_format_name: decimal_2
  }
  measure: reports { type: count }
  measure: flagged {
    type: count
    filters: [status: "ets_exceeds_reported"]
  }
}
