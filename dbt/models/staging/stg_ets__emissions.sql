select
    registry_code,
    installation_id,
    registry_code || lpad(installation_id, 15, '0') as ets_identifier,
    account_holder,
    installation_name,
    permit_id,
    activity_code,
    year as reporting_year,
    verified_t,
    allocation_t,
    status
from {{ source('raw', 'ets_emissions') }}
