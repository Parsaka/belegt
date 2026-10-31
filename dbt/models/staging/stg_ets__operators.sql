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
    contact_country,
    -- Excel may store a German postcode as a number and drop its leading zero (01067 -> 1067).
    case
        when contact_country = 'DE' then lpad(trim(postcode), 5, '0')
        else postcode
    end as postcode
from {{ source('raw', 'ets_operators') }}
