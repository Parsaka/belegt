view: legal_entities {
  sql_table_name: `marts.dim_legal_entity` ;;

  dimension: legal_entity_key { primary_key: yes hidden: yes sql: ${TABLE}.legal_entity_key ;; }
  dimension: lei { sql: ${TABLE}.lei ;; }
  dimension: legal_name { sql: ${TABLE}.legal_name ;; }
  dimension: country { sql: ${TABLE}.country ;; }
  dimension: city { sql: ${TABLE}.city ;; }
  dimension: legal_form { sql: ${TABLE}.legal_form ;; }
  dimension: entity_status { sql: ${TABLE}.entity_status ;; }
  dimension: is_current {
    description: "SCD2: the version valid today."
    type: yesno
    sql: ${TABLE}.is_current ;;
  }
  dimension_group: valid_from { type: time timeframes: [date, month, year] sql: ${TABLE}.valid_from ;; }
}
