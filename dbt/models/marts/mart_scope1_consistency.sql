-- Reported Scope 1 next to the verified ETS emissions of the same group and year.
--
-- The ETS figure covers the group's German installations only, while Scope 1 is worldwide, so
-- ETS above the reported figure is a contradiction worth a look; ETS below it is expected.
-- The tolerance (5 %) covers figures that reports round to 0.1 Mt.
with scope1 as (
    select * from {{ ref('fct_reported_metric') }} where metric = 'scope1'
)

select
    r.doc_id,
    r.company,
    r.lei,
    r.report_year,
    s.value_t as reported_scope1_t,
    s.page as reported_page,
    s.quote as reported_quote,
    s.figure_source,
    s.column_year is null and s.figure_source = 'extracted' as needs_review,
    g.verified_t as ets_verified_t,
    g.installations as ets_installations,
    case when s.value_t > 0 then g.verified_t / s.value_t end as ets_share_of_reported,
    case
        when s.value_t is null then 'no_reported_figure'
        when g.verified_t is null then 'no_ets_group'
        when g.verified_t > s.value_t * 1.05 then 'ets_exceeds_reported'
        else 'consistent'
    end as status,
    case
        when r.fiscal_year_end != '12-31'
            then 'Fiscal year ends ' || r.fiscal_year_end || '; ETS years are calendar years.'
    end as caveat
from {{ ref('reports') }} as r
left join scope1 as s using (doc_id)
left join {{ ref('mart_group_emissions') }} as g
    on g.group_lei = r.lei and g.reporting_year = r.report_year
