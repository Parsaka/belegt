{# Rolling up must neither drop nor double-count tonnes of matched installations.
   (`groups` is a reserved word in BigQuery, hence `rolled_up`.) #}
{% test group_total_matches_attributed_facts(model) %}
with facts as (
    select f.reporting_year, sum(f.verified_t) as t
    from {{ ref('fct_verified_emissions') }} as f
    inner join {{ ref('dim_installation') }} as d using (ets_identifier)
    where d.match_decision = 'accepted' and f.is_reported
    group by 1
),
rolled_up as (
    select reporting_year, sum(verified_t) as t from {{ model }} group by 1
)
select reporting_year, facts.t as facts_t, rolled_up.t as groups_t
from facts full outer join rolled_up using (reporting_year)
where coalesce(facts.t, -1) <> coalesce(rolled_up.t, -1)
{% endtest %}
