-- One row per ETS installation, with the latest registry attributes and the EEA site data.
with latest as (
    select
        *,
        row_number() over (
            partition by ets_identifier order by reporting_year desc
        ) as rn
    from {{ ref('stg_ets__emissions') }}
)

select
    l.ets_identifier,
    l.installation_id,
    l.registry_code,
    l.installation_name,
    l.account_holder,
    l.permit_id,
    l.activity_code,
    e.installation_inspire_id,
    e.facility_name,
    e.parent_company_name,
    e.city,
    e.lat,
    e.lon,
    ie.lei as operator_lei,
    ie.match_decision,
    ie.match_score,
    e.installation_inspire_id is not null as is_in_eea
from latest as l
left join {{ ref('stg_eea__installations') }} as e using (ets_identifier)
left join {{ ref('int_installation_entity') }} as ie using (ets_identifier)
where l.rn = 1
