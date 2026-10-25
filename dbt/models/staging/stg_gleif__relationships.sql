-- Open-ended periods get a far-future end so range joins need no null handling.
select
    child_lei,
    parent_lei,
    case relationship_type
        when 'IS_DIRECTLY_CONSOLIDATED_BY' then 'direct'
        when 'IS_ULTIMATELY_CONSOLIDATED_BY' then 'ultimate'
    end as relationship_kind,
    coalesce(valid_from, date '1900-01-01') as valid_from,
    coalesce(valid_to, date '9999-12-31') as valid_to,
    status,
    registration_status
from {{ source('raw', 'gleif_relationships') }}
where status = 'ACTIVE' or valid_to is not null
