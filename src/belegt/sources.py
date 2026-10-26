"""Registry of every dataset Belegt uses, with its origin and licence.

`docs/data-sources.md` is the human-readable version; both must stay in sync.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class Verification(StrEnum):
    VERIFIED = "verified"  # licence and access checked on the publisher's own page
    PARTIAL = "partial"  # access checked, a detail (granularity, terms) still open
    UNVERIFIED = "unverified"


@dataclass(frozen=True)
class Source:
    id: str
    name: str
    publisher: str
    url: str
    licence: str
    attribution: str
    verification: Verification
    open_question: str | None = None


SOURCES: tuple[Source, ...] = (
    Source(
        id="eu_ets_union_registry",
        name="EU ETS verified emissions and compliance data",
        publisher="European Commission, DG CLIMA (Union Registry)",
        url="https://climate.ec.europa.eu/areas-action/carbon-markets/eu-emissions-trading-system-eu-ets/union-registry_en",
        licence="Commission reuse policy (Decision 2011/833/EU), reuse with attribution",
        attribution="Source: European Commission, Union Registry",
        verification=Verification.VERIFIED,
    ),
    Source(
        id="eu_ets_operators",
        name="EU ETS installation operators (account holder, register number, LEI)",
        publisher="European Commission, DG CLIMA (Union Registry)",
        url="https://climate.ec.europa.eu/areas-action/carbon-markets/eu-emissions-trading-system-eu-ets/union-registry_en",
        licence="Commission reuse policy (Decision 2011/833/EU), reuse with attribution",
        attribution="Source: European Commission, Union Registry",
        verification=Verification.VERIFIED,
    ),
    Source(
        id="eea_industrial_reporting",
        name="Industrial Reporting under the IED and E-PRTR (tabular data)",
        publisher="European Environment Agency",
        url="https://sdi.eea.europa.eu/catalogue/srv/api/records/ff47e25d-5d4c-491d-b9ce-de17ca61fe6d",
        licence="CC BY 4.0",
        attribution="Source: European Environment Agency (EEA)",
        verification=Verification.VERIFIED,
    ),
    Source(
        id="gleif_golden_copy",
        name="GLEIF Golden Copy, Level 1 (LEI-CDF) and Level 2 (RR-CDF)",
        publisher="Global Legal Entity Identifier Foundation",
        url="https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy",
        licence="CC0 1.0",
        attribution="Source: GLEIF (no endorsement implied)",
        verification=Verification.VERIFIED,
    ),
    Source(
        id="esrs_eurlex",
        name="ESRS, Commission Delegated Regulation (EU) 2023/2772",
        publisher="Publications Office of the European Union (EUR-Lex)",
        url="https://eur-lex.europa.eu/eli/reg_del/2023/2772/oj",
        licence="EU legal text, reuse with attribution",
        attribution="Source: EUR-Lex, (EU) 2023/2772",
        verification=Verification.VERIFIED,
    ),
    Source(
        id="sustainability_statements",
        name="Sustainability statements in the annual reports of German ETS-heavy groups",
        publisher="The reporting companies (annual report PDFs on their investor-relations hosts)",
        url="https://github.com/Parsaka/belegt/blob/main/dbt/seeds/reports.csv",
        licence="Copyrighted; PDFs only in the private bucket, Git holds links and metadata",
        attribution="Source: the company's annual report, page cited per figure and answer",
        verification=Verification.PARTIAL,
        open_question=(
            "Each link is checked by the Reports workflow (it must return a PDF); links "
            "outside the company's own site are used only where it offers none."
        ),
    ),
)


def get(source_id: str) -> Source:
    for source in SOURCES:
        if source.id == source_id:
            return source
    raise KeyError(f"unknown source: {source_id}")
