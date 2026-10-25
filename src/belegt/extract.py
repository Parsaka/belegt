"""Download the full German source files that `belegt load` reads.

Runs in GitHub Actions (the publishers are not reachable from every network). The output
directory has the same file names as `tests/fixtures/`, so the loaders cannot tell a fixture from
a full extract. Every file is listed in `manifest.json` with its source URL and SHA-256, so each
row in the warehouse can be traced back to the exact file it came from.

Re-runs overwrite the directory: the extract is idempotent for a given publisher release.
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import shutil
import subprocess
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from itertools import chain
from pathlib import Path
from typing import IO, Any
from urllib.parse import urljoin

USER_AGENT = "belegt/0.1 (ESG portfolio project; +https://github.com/Parsaka/belegt)"
UR_PAGE = (
    "https://climate.ec.europa.eu/areas-action/carbon-markets/"
    "eu-emissions-trading-system-eu-ets/union-registry_en"
)
OPERATORS_FILE = "policy_ets_registry_operators_ets_en.xlsx"
_VERIFIED = re.compile(r"verified_emissions_(\d{4})_en\.xlsx$")
EEA_SHARE = "https://sdi.eea.europa.eu/datashare/public.php/webdav/"
EEA_SHARE_TOKEN = "sptXqwkQr5g7Bp5"  # the public share id, not a secret
EEA_ACCDB = "eea_t_ied-eprtr_p_2007-2024_v16_r00/Industrial_dataset_v_16_2026_02_16.accdb"
GLEIF_LATEST = "https://goldencopy.gleif.org/api/v2/golden-copies/publishes/latest"
# ESRS, Delegated Regulation (EU) 2023/2772, German Official Journal PDF. EU legal text may be
# reused with attribution. Two addresses for the same file: EUR-Lex sometimes answers automated
# requests with a challenge page instead of the PDF.
ESRS_PDF_URLS = (
    "https://eur-lex.europa.eu/legal-content/DE/TXT/PDF/?uri=OJ:L_202302772",
    "https://eur-lex.europa.eu/eli/reg_del/2023/2772/oj/deu/pdf",
)

# Golden-copy LEI-CDF columns the loader needs. Checked against the file header on every run.
LEI_COLUMNS = (
    "LEI",
    "Entity.LegalName",
    "Entity.LegalAddress.City",
    "Entity.LegalAddress.Country",
    "Entity.RegistrationAuthority.RegistrationAuthorityID",
    "Entity.RegistrationAuthority.RegistrationAuthorityEntityID",
    "Entity.LegalForm.EntityLegalFormCode",
    "Entity.EntityStatus",
    "Registration.RegistrationStatus",
    "Registration.LastUpdateDate",
)
CONSOLIDATION = {"IS_DIRECTLY_CONSOLIDATED_BY", "IS_ULTIMATELY_CONSOLIDATED_BY"}


@dataclass(frozen=True)
class Extracted:
    file: str
    source_url: str
    sha256: str
    bytes: int
    rows: int | None = None


# --- pure filters (unit-tested offline) ------------------------------------------------------


def latest_verified_emissions(links: Iterable[str]) -> str:
    """The newest `verified_emissions_<year>_en.xlsx` link on the Union Registry page."""
    found = [(int(m.group(1)), link) for link in links if (m := _VERIFIED.search(link))]
    if not found:
        raise ValueError("no verified_emissions_<year>_en.xlsx link on the Union Registry page")
    return max(found)[1]


def consolidation_parents(rr_rows: Iterable[dict[str, str]]) -> set[str]:
    """Every LEI that consolidates another one, so foreign group parents are kept too."""
    return {
        r["Relationship.EndNode.NodeID"]
        for r in rr_rows
        if r["Relationship.RelationshipType"] in CONSOLIDATION
    }


def check_columns(header: Iterable[str], required: Iterable[str], what: str) -> None:
    missing = sorted(set(required) - set(header))
    if missing:
        raise ValueError(f"{what}: the publisher changed the format, missing columns {missing}")


def select_entities(
    rows: Iterable[dict[str, str]], parents: set[str], country: str = "DE"
) -> Iterator[dict[str, str]]:
    """German legal entities plus every group parent, reduced to the columns the loader reads."""
    for r in rows:
        if r["Entity.LegalAddress.Country"] == country or r["LEI"] in parents:
            yield {c: r[c] for c in LEI_COLUMNS}


def select_relationships(
    rr_rows: Iterable[dict[str, str]], children: set[str]
) -> Iterator[dict[str, str]]:
    """Consolidation edges whose child is one of the kept entities, without the bulky
    qualifier and quantifier columns."""
    for r in rr_rows:
        if (
            r["Relationship.RelationshipType"] in CONSOLIDATION
            and r["Relationship.StartNode.NodeID"] in children
        ):
            yield {k: v for k, v in r.items() if not re.search(r"Qualifiers|Quantifiers", k)}


def select_eea(
    ets_ids: list[dict[str, str]],
    installations: list[dict[str, str]],
    facilities: list[dict[str, str]],
    country: str = "DE",
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    """Follow the German ETS ids through installation to facility, as the loader expects."""
    links = [r for r in ets_ids if r["ETSIdentifier"].strip().startswith(country)]
    inst_ids = {r["Installation_INSPIRE_ID"] for r in links}
    inst = [r for r in installations if r["Installation_INSPIRE_ID"] in inst_ids]
    fac_ids = {r["Parent_Facility_INSPIRE_ID"] for r in inst}
    fac = [r for r in facilities if r["Facility_INSPIRE_ID"] in fac_ids]
    return links, inst, fac


# --- I/O --------------------------------------------------------------------------------------


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_csv(path: Path, rows: Iterable[dict[str, str]]) -> int:
    n = 0
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer: csv.DictWriter[str] | None = None
        for row in rows:
            if writer is None:
                writer = csv.DictWriter(fh, fieldnames=list(row))
                writer.writeheader()
            writer.writerow(row)
            n += 1
    return n


def _record(out: Path, name: str, url: str, rows: int | None = None) -> Extracted:
    path = out / name
    return Extracted(name, url, _sha256(path), path.stat().st_size, rows)


def _csv_in_zip(blob: IO[bytes]) -> Iterator[dict[str, str]]:
    with zipfile.ZipFile(blob) as z, z.open(z.namelist()[0]) as fh:
        yield from csv.DictReader(io.TextIOWrapper(fh, "utf-8", newline=""))


def _download(client: Any, url: str, path: Path, **kwargs: Any) -> None:
    with client.stream("GET", url, **kwargs) as r:
        r.raise_for_status()
        with path.open("wb") as fh:
            for chunk in r.iter_bytes(1 << 20):
                fh.write(chunk)


def extract_ets(client: Any, out: Path) -> list[Extracted]:
    html = client.get(UR_PAGE).text
    links = [urljoin(UR_PAGE, x) for x in re.findall(r'href="([^"]+)"', html)]
    verified = latest_verified_emissions(links)
    operators = next(x for x in links if x.endswith(OPERATORS_FILE))
    # Whole workbooks, unchanged: the loader selects the German rows.
    _download(client, verified, out / "ets_verified_emissions_de.xlsx")
    _download(client, operators, out / "ets_operators_de.xlsx")
    return [
        _record(out, "ets_verified_emissions_de.xlsx", verified),
        _record(out, "ets_operators_de.xlsx", operators),
    ]


def _mdb_export(accdb: Path, table: str) -> list[dict[str, str]]:
    raw = subprocess.run(["mdb-export", str(accdb), table], capture_output=True, check=True)
    return list(csv.DictReader(io.StringIO(raw.stdout.decode("utf-8", "replace"))))


def extract_eea(client: Any, out: Path, work: Path) -> list[Extracted]:
    if not shutil.which("mdb-export"):
        raise RuntimeError("mdb-export is missing (apt-get install mdbtools)")
    url = EEA_SHARE + EEA_ACCDB
    accdb = work / "eea.accdb"
    _download(client, url, accdb, auth=(EEA_SHARE_TOKEN, ""))
    links, inst, fac = select_eea(
        _mdb_export(accdb, "3f2_ETSIdentifiers"),
        _mdb_export(accdb, "3_ProductionInstallation"),
        _mdb_export(accdb, "2_ProductionFacility"),
    )
    found = []
    for name, rows in (
        ("eea_ets_identifiers.csv", links),
        ("eea_installations.csv", inst),
        ("eea_facilities.csv", fac),
    ):
        found.append(_record(out, name, url, write_csv(out / name, rows)))
    return found


def extract_gleif(client: Any, out: Path, work: Path) -> list[Extracted]:
    files = client.get(GLEIF_LATEST).json()["data"]
    lei_url = files["lei2"]["full_file"]["csv"]["url"]
    rr_url = files["rr"]["full_file"]["csv"]["url"]
    _download(client, rr_url, work / "rr.zip")
    _download(client, lei_url, work / "lei2.zip")

    with (work / "rr.zip").open("rb") as fh:
        parents = consolidation_parents(_csv_in_zip(fh))
    kept: set[str] = set()
    with (work / "lei2.zip").open("rb") as fh:
        rows = _csv_in_zip(fh)
        first = next(rows)
        check_columns(first, LEI_COLUMNS, "GLEIF LEI-CDF golden copy")

        def tracked() -> Iterator[dict[str, str]]:
            for r in select_entities(chain([first], rows), parents):
                kept.add(r["LEI"])
                yield r

        n_entities = write_csv(out / "gleif_entities.csv", tracked())
    with (work / "rr.zip").open("rb") as fh:
        n_rr = write_csv(out / "gleif_rr.csv", select_relationships(_csv_in_zip(fh), kept))
    return [
        _record(out, "gleif_entities.csv", lei_url, n_entities),
        _record(out, "gleif_rr.csv", rr_url, n_rr),
    ]


def is_pdf(head: bytes) -> bool:
    return head.startswith(b"%PDF-")


def extract_esrs(client: Any, out: Path) -> list[Extracted]:
    path = out / "esrs_de.pdf"
    for url in ESRS_PDF_URLS:
        _download(client, url, path)
        with path.open("rb") as fh:
            if is_pdf(fh.read(5)):
                return [_record(out, path.name, url)]
    path.unlink(missing_ok=True)
    raise RuntimeError("EUR-Lex returned no PDF for the ESRS (challenge page?)")


def extract_all(out: Path, work: Path) -> list[Extracted]:
    import httpx

    out.mkdir(parents=True, exist_ok=True)
    work.mkdir(parents=True, exist_ok=True)
    found: list[Extracted] = []
    with httpx.Client(
        headers={"User-Agent": USER_AGENT}, timeout=600, follow_redirects=True
    ) as client:
        found += extract_ets(client, out)
        found += extract_eea(client, out, work)
        found += extract_gleif(client, out, work)
        found += extract_esrs(client, out)
    manifest = {
        "extracted_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "files": [asdict(f) for f in found],
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return found
