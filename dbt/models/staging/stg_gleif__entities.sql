select
    lei,
    legal_name,
    country,
    city,
    registered_as,
    registered_at,
    legal_form,
    entity_status,
    registration_status,
    cast(last_update as timestamp) as last_update
from {{ source('raw', 'gleif_entities') }}
