-- One figure per report and metric, with the page and table line it came from: a reviewed
-- correction where a person checked the page, otherwise the candidate the extractor selected.
with extracted as (
    select * from {{ ref('stg_reported_metrics') }} where selected
),

reviewed as (
    select * from {{ ref('reported_overrides') }}
),

figures as (
    select
        coalesce(o.doc_id, e.doc_id) as doc_id,
        coalesce(o.metric, e.metric) as metric,
        coalesce(o.value_t, e.value_t) as value_t,
        coalesce(o.page, e.page) as page,
        coalesce(o.quote, e.quote) as quote,
        e.unit_raw,
        e.column_year,
        case when o.doc_id is not null then 'reviewed' else 'extracted' end as figure_source,
        o.reviewer
    from extracted as e
    full outer join reviewed as o
        on o.doc_id = e.doc_id and o.metric = e.metric
)

select
    r.doc_id,
    r.company,
    r.lei,
    r.report_year,
    r.fiscal_year_end,
    f.metric,
    f.value_t,
    f.page,
    f.unit_raw,
    f.quote,
    f.column_year,
    f.figure_source,
    f.reviewer,
    r.url
from figures as f
inner join {{ ref('reports') }} as r using (doc_id)
