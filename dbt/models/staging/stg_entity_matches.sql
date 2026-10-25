-- A reviewer's decision in the seed always replaces the automatic one.
select
    m.source_name,
    case when o.source_name is not null then o.lei else m.lei end as lei,
    m.score,
    coalesce(o.decision, m.decision) as decision,
    case when o.source_name is not null then 'override' else 'automatic' end as decided_by,
    m.evidence
from {{ source('raw', 'entity_matches') }} as m
left join {{ ref('entity_overrides') }} as o using (source_name)
