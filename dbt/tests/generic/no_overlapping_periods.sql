{# A child may not have two parents of the same kind in overlapping periods. #}
{% test no_overlapping_periods(model) %}
select a.child_lei, a.relationship_kind, a.parent_lei, b.parent_lei as other_parent
from {{ model }} as a
inner join {{ model }} as b
    on a.child_lei = b.child_lei
    and a.relationship_kind = b.relationship_kind
    and a.parent_lei < b.parent_lei
    and a.valid_from <= b.valid_to
    and b.valid_from <= a.valid_to
{% endtest %}
