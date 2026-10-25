{# md5 over the joined columns; same result on DuckDB and BigQuery (to_hex(md5(...))). #}
{% macro dbt_utils_surrogate_key(columns) -%}
    {%- set joined -%}
        concat({% for c in columns %}coalesce(cast({{ c }} as {{ dbt.type_string() }}), '_null_'){% if not loop.last %}, '|', {% endif %}{% endfor %})
    {%- endset -%}
    {%- if target.type == 'bigquery' -%}
        to_hex(md5({{ joined }}))
    {%- else -%}
        md5({{ joined }})
    {%- endif -%}
{%- endmacro %}
