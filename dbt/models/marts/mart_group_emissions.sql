-- Verified emissions rolled up to the ultimate parent that consolidated the operator that year.
-- An operator without an ultimate parent in GLEIF is its own group.
with operator_year as (
    select
        f.ets_identifier,
        f.reporting_year,
        f.verified_t,
        d.operator_lei
    from {{ ref('fct_verified_emissions') }} as f
    inner join {{ ref('dim_installation') }} as d using (ets_identifier)
    where d.match_decision = 'accepted' and f.is_reported
),

ultimate as (
    select
        o.*,
        b.parent_lei,
        b.relationship_kind,
        row_number() over (
            partition by o.ets_identifier, o.reporting_year
            order by case b.relationship_kind when 'ultimate' then 0 else 1 end
        ) as rn
    from operator_year as o
    inner join {{ ref('bridge_ownership') }} as b
        on b.child_lei = o.operator_lei
        and b.relationship_kind in ('ultimate', 'self')
        and {{ year_end('o.reporting_year') }} between b.valid_from and b.valid_to
)

select
    u.parent_lei as group_lei,
    e.legal_name as group_name,
    u.reporting_year,
    sum(u.verified_t) as verified_t,
    count(distinct u.ets_identifier) as installations
from ultimate as u
left join {{ ref('stg_gleif__entities') }} as e on e.lei = u.parent_lei
where u.rn = 1
group by 1, 2, 3
