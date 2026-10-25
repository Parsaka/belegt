-- Grain: one installation, one reporting year. Unreported years keep a status and a null value.
select
    ets_identifier,
    reporting_year,
    verified_t,
    allocation_t,
    status,
    verified_t is not null as is_reported
from {{ ref('stg_ets__emissions') }}
