-- One approximate point per German postcode (GeoNames, CC BY 4.0).
-- GeoNames mixes English and German state names ("Bavaria", "Hessen"); the seed gives the
-- official German name for each two-letter code.
select
    p.postcode,
    p.place,
    p.state_code,
    coalesce(s.state_name, p.state) as state,
    p.lat,
    p.lon
from {{ source('raw', 'postcodes') }} as p
left join {{ ref('states') }} as s using (state_code)
