select
    doc_id,
    metric,
    value_t,
    page,
    unit_raw,
    quote,
    rows_on_page,
    selected
from {{ source('raw', 'reported_metrics') }}
