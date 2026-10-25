-- Installation -> operating legal entity. The registry's account holder is the primary path;
-- the EEA parent company name (Brandenburg only) is used where the account holder found no match.
with candidates as (
    select
        o.ets_identifier,
        o.account_holder as source_name,
        'registry account holder' as path,
        1 as priority
    from {{ ref('stg_ets__operators') }} as o

    union all

    select
        i.ets_identifier,
        i.parent_company_name as source_name,
        'EEA parent company' as path,
        2 as priority
    from {{ ref('stg_eea__installations') }} as i
    where i.parent_company_name is not null
),

scored as (
    select
        c.ets_identifier,
        c.source_name,
        c.path,
        m.lei,
        m.score as match_score,
        m.decision as match_decision,
        m.decided_by,
        m.evidence,
        row_number() over (
            partition by c.ets_identifier
            order by case m.decision when 'accepted' then 0 when 'review' then 1 else 2 end, c.priority
        ) as rn
    from candidates as c
    left join {{ ref('stg_entity_matches') }} as m on c.source_name = m.source_name
)

select ets_identifier, source_name, path, lei, match_score, match_decision, decided_by, evidence
from scored
where rn = 1
