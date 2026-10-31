"""GeoNames postal codes for Germany (CC BY 4.0): one approximate point per postcode.

The EEA links only 49 German ETS installations to a facility with coordinates, so the map
falls back to the postcode of the registry contact address. The file is GeoNames' `DE.txt`,
tab-separated without a header; a postcode spanning several places gets the mean of their
points and the first place name.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

# country, postal code, place, admin1 name, admin1 code, admin2 name, admin2 code,
# admin3 name, admin3 code, latitude, longitude, accuracy
_POSTCODE, _PLACE, _STATE, _LAT, _LON = 1, 2, 3, 9, 10


@dataclass(frozen=True)
class Postcode:
    postcode: str
    place: str
    state: str | None
    lat: float
    lon: float


def parse_lines(lines: Iterable[str]) -> Iterator[Postcode]:
    places: dict[str, list[list[str]]] = {}
    for line in lines:
        if line.strip():
            fields = line.rstrip("\n").split("\t")
            places.setdefault(fields[_POSTCODE].strip(), []).append(fields)
    for code, rows in places.items():
        yield Postcode(
            postcode=code,
            place=rows[0][_PLACE].strip(),
            state=rows[0][_STATE].strip() or None,
            lat=round(sum(float(r[_LAT]) for r in rows) / len(rows), 5),
            lon=round(sum(float(r[_LON]) for r in rows) / len(rows), 5),
        )


def read_postcodes(path: Path) -> Iterator[Postcode]:
    with path.open(encoding="utf-8") as fh:
        yield from parse_lines(fh)
