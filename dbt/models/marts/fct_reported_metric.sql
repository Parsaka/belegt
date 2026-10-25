-- One figure per report and metric: the candidate the extractor selected (the E1-6 table),
-- with the page and table line it came from.
select
    r.doc_id,
    r.company,
    r.lei,
    r.report_year,
    r.fiscal_year_end,
    m.metric,
    m.value_t,
    m.page,
    m.unit_raw,
    m.quote,
    r.url
from {{ ref('stg_reported_metrics') }} as m
inner join {{ ref('reports') }} as r using (doc_id)
where m.selected
