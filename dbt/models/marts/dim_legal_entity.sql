-- SCD2: one row per version of a legal entity. Join facts on lei and the period that covers them.
select
    {{ dbt_utils_surrogate_key(['lei', 'dbt_valid_from']) }} as legal_entity_key,
    lei,
    legal_name,
    country,
    city,
    registered_as,
    legal_form,
    entity_status,
    cast(dbt_valid_from as timestamp) as valid_from,
    cast(coalesce(dbt_valid_to, timestamp '9999-12-31') as timestamp) as valid_to,
    dbt_valid_to is null as is_current
from {{ ref('snap_gleif_entities') }}
