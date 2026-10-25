{% test one_current_version_per_lei(model) %}
select lei from {{ model }} where is_current group by lei having count(*) > 1
{% endtest %}
