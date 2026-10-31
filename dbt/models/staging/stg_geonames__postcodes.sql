-- One approximate point per German postcode (GeoNames, CC BY 4.0).
select
    postcode,
    place,
    state,
    lat,
    lon
from {{ source('raw', 'postcodes') }}
