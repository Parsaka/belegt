-- Installation -> operating legal entity, through the EEA parent company name.
select
    i.ets_identifier,
    i.parent_company_name,
    m.lei,
    m.score as match_score,
    m.decision as match_decision,
    m.decided_by
from {{ ref('stg_eea__installations') }} as i
left join {{ ref('stg_entity_matches') }} as m
    on i.parent_company_name = m.source_name
