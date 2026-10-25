{% snapshot snap_gleif_entities %}
{#
  SCD2 history of legal entities. GLEIF bumps lastUpdateDate whenever a record changes
  (name, address, status), so a new version opens exactly when the publisher says it changed.
#}
{{
    config(
        target_schema='snapshots',
        unique_key='lei',
        strategy='timestamp',
        updated_at='last_update',
        invalidate_hard_deletes=True,
    )
}}
select * from {{ ref('stg_gleif__entities') }}
{% endsnapshot %}
