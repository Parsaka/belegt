-- Time-bounded consolidation edges. A child can move between groups; each period is one row.
-- Every entity is also its own ultimate parent, so groups without a GLEIF parent roll up to self.
select
    child_lei,
    parent_lei,
    relationship_kind,
    valid_from,
    valid_to
from {{ ref('stg_gleif__relationships') }}

union all

select
    lei as child_lei,
    lei as parent_lei,
    'self' as relationship_kind,
    date '1900-01-01' as valid_from,
    date '9999-12-31' as valid_to
from {{ ref('stg_gleif__entities') }}
