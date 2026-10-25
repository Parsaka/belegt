select
    registry_code,
    installation_id,
    registry_code || lpad(installation_id, 15, '0') as ets_identifier,
    account_holder,
    register_nr,
    lei as registry_lei,
    activity_type,
    permit_id,
    permit_status,
    city,
    postcode
from {{ source('raw', 'ets_operators') }}
