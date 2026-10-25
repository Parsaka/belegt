-- One row per ETS identifier: the installation it pointed to in its latest EEA reporting year.
with ranked as (
    select
        l.ets_identifier,
        l.installation_inspire_id,
        l.reporting_year,
        row_number() over (
            partition by l.ets_identifier order by l.reporting_year desc
        ) as rn
    from {{ source('raw', 'eea_ets_links') }} as l
)

select
    r.ets_identifier,
    r.installation_inspire_id,
    r.reporting_year as eea_reporting_year,
    i.facility_inspire_id,
    i.name as eea_installation_name,
    i.activity_code as ied_activity_code,
    f.name as facility_name,
    f.parent_company_name,
    f.city,
    f.country,
    f.lat,
    f.lon
from ranked as r
left join {{ source('raw', 'eea_installations') }} as i using (installation_inspire_id)
left join {{ source('raw', 'eea_facilities') }} as f using (facility_inspire_id)
where r.rn = 1
