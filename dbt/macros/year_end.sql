{# 31 December of an integer year; the two warehouses name this function differently. #}
{% macro year_end(year) -%}
    {%- if target.type == 'bigquery' -%} date({{ year }}, 12, 31)
    {%- else -%} make_date(cast({{ year }} as integer), 12, 31)
    {%- endif -%}
{%- endmacro %}
