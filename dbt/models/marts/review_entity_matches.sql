-- The review queue: names without a confident match and without a human decision yet.
select
    m.source_name,
    m.lei as suggested_lei,
    e.legal_name as suggested_name,
    m.score,
    m.evidence,
    count(distinct i.ets_identifier) as installations
from {{ ref('stg_entity_matches') }} as m
left join {{ ref('stg_gleif__entities') }} as e using (lei)
left join {{ ref('stg_eea__installations') }} as i on i.parent_company_name = m.source_name
where m.decision = 'review' and m.decided_by = 'automatic'
group by 1, 2, 3, 4, 5
