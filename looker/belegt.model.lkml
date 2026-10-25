# Semantic layer over the dbt marts in BigQuery. dbt owns the tables and their tests; LookML
# owns the business definitions (what "attributed", "match rate" and "consistent" mean).
connection: "belegt"

include: "/views/*.view.lkml"

# The marts change once a month. No SQL trigger: a trigger query every few minutes would spend
# BigQuery quota for nothing.
datagroup: monthly_marts {
  max_cache_age: "24 hours"
}
persist_with: monthly_marts

explore: installations {
  label: "ETS installations"
  description: "Every German ETS account with its verified emissions and the company that operates it."

  join: verified_emissions {
    type: left_outer
    relationship: one_to_many
    sql_on: ${verified_emissions.ets_identifier} = ${installations.ets_identifier} ;;
  }

  join: operator {
    from: legal_entities
    type: left_outer
    relationship: many_to_one
    sql_on: ${operator.lei} = ${installations.operator_lei} AND ${operator.is_current} ;;
  }
}

explore: group_emissions {
  label: "Group emissions"
  description: "Verified ETS emissions rolled up to the ultimate parent that consolidated the operator that year."
}

explore: scope1_consistency {
  label: "Reported vs verified"
  description: "Scope 1 from sustainability statements against verified ETS emissions of the same group."

  join: reported_metrics {
    type: left_outer
    relationship: one_to_many
    sql_on: ${reported_metrics.doc_id} = ${scope1_consistency.doc_id} ;;
  }
}
