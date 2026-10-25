select
    doc_id,
    metric,
    value_t,
    page,
    unit_raw,
    quote,
    rows_on_page,
    selected,
    column_year
from {{ source('raw', 'reported_metrics') }}
