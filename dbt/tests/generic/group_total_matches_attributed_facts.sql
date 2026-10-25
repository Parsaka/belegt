{# Rolling up must neither drop nor double-count tonnes of matched installations. #}
{% test group_total_matches_attributed_facts(model) %}
with facts as (
    select f.reporting_year, sum(f.verified_t) as t
    from {{ ref('fct_verified_emissions') }} as f
    inner join {{ ref('dim_installation') }} as d using (ets_identifier)
    where d.match_decision = 'accepted' and f.is_reported
    group by 1
),
groups as (
    select reporting_year, sum(verified_t) as t from {{ model }} group by 1
)
select * from facts full outer join groups using (reporting_year)
where coalesce(facts.t, -1) <> coalesce(groups.t, -1)
{% endtest %}
