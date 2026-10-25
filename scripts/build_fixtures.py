"""Build trimmed real fixtures for the loaders (runs in GitHub Actions, which has network access).

Picks German ETS installations of a few known groups plus some others, and follows them through
the EEA Industrial Reporting database (ETS id -> installation -> facility -> parent company).
Also prints link statistics for all German installations so docs can quote measured numbers.
"""

from __future__ import annotations

import csv
import io
import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urljoin

import httpx
from openpyxl import Workbook, load_workbook

UA = {"User-Agent": "belegt-portfolio/0.1 (+https://github.com/Parsaka/belegt)"}
OUT = Path("inspect/fixtures")
OUT.mkdir(parents=True, exist_ok=True)
client = httpx.Client(headers=UA, timeout=300, follow_redirects=True)
GROUPS = re.compile(r"BASF|Heidelberg|RWE", re.I)
UR_PAGE = "https://climate.ec.europa.eu/areas-action/carbon-markets/eu-emissions-trading-system-eu-ets/union-registry_en"
ACCDB = sys.argv[1] if len(sys.argv) > 1 else "/tmp/eea.accdb"


def ets_rows() -> tuple[list[tuple[object, ...]], int, list[tuple[object, ...]]]:
    html = client.get(UR_PAGE).text
    links = re.findall(r'href="([^"]+)"', html)
    url = next(urljoin(UR_PAGE, x) for x in links if x.endswith("verified_emissions_2025_en.xlsx"))
    wb = load_workbook(io.BytesIO(client.get(url).content), read_only=True, data_only=True)
    rows = list(wb.worksheets[0].iter_rows(values_only=True))
    hdr_i = next(i for i, r in enumerate(rows) if r and r[0] == "REGISTRY_CODE")
    return rows[:hdr_i], hdr_i, rows[hdr_i:]


def ets_key(installation_id: object) -> str:
    """Union Registry id 1231 -> EEA ETSIdentifier DE000000000001231."""
    return f"DE{int(str(installation_id).strip()):015d}"


def export(table: str) -> list[dict[str, str]]:
    raw = subprocess.run(["mdb-export", ACCDB, table], capture_output=True, check=True).stdout
    return list(csv.DictReader(io.StringIO(raw.decode("utf-8", "replace"))))


def write_csv(name: str, rows: list[dict[str, str]]) -> None:
    if not rows:
        print("empty:", name)
        return
    with (OUT / name).open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    preamble, hdr_i, table = ets_rows()
    hdr = table[0]
    col = {name: i for i, name in enumerate(hdr)}
    de = [r for r in table[1:] if r and r[0] == "DE" and str(r[col["ACCOUNT_TYPE"]]).upper().startswith("OPERATOR HOLDING")]
    if not de:  # account type labels differ between releases
        de = [r for r in table[1:] if r and r[0] == "DE" and not r[col["IMO_NUMBER"]]]
    picked = [r for r in de if GROUPS.search(f"{r[col['IDENTIFIER_IN_REG']]} {r[col['INSTALLATION_NAME']]}")][:24]
    picked += [r for r in de if r not in picked][:: max(1, len(de) // 8)][:8]
    print(f"ETS: header at row {hdr_i}, {len(de)} German stationary rows, {len(picked)} picked")

    wb = Workbook()
    ws = wb.active
    ws.title = "data"
    for r in [*preamble, hdr, *picked]:
        ws.append(list(r))
    wb.save(OUT / "ets_verified_emissions_de.xlsx")

    ets_ids = export("3f2_ETSIdentifiers")
    inst = {r["Installation_INSPIRE_ID"]: r for r in export("3_ProductionInstallation")}
    fac = {r["Facility_INSPIRE_ID"]: r for r in export("2_ProductionFacility")}
    de_ets = [r for r in ets_ids if r["ETSIdentifier"].startswith("DE")]

    # link statistics over all German ETS installations (latest EEA year per id)
    latest: dict[str, dict[str, str]] = {}
    for r in de_ets:
        if r["ETSIdentifier"] not in latest or r["reportingYear"] > latest[r["ETSIdentifier"]]["reportingYear"]:
            latest[r["ETSIdentifier"]] = r
    ur_ids = {ets_key(r[col["INSTALLATION_IDENTIFIER"]]) for r in de}
    linked = [latest[i] for i in ur_ids if i in latest]
    with_parent = [
        r for r in linked
        if (f := fac.get(inst.get(r["Installation_INSPIRE_ID"], {}).get("Parent_Facility_INSPIRE_ID", "")))
        and f.get("parentCompanyName")
    ]
    parents = Counter(
        fac[inst[r["Installation_INSPIRE_ID"]]["Parent_Facility_INSPIRE_ID"]]["parentCompanyName"]
        for r in with_parent
    )
    stats = {
        "ets_de_stationary_installations": len(ur_ids),
        "eea_de_ets_identifiers": len(latest),
        "ets_installations_found_in_eea": len(linked),
        "with_parent_company_name": len(with_parent),
        "distinct_parent_company_names": len(parents),
        "eea_reporting_years": sorted({r["reportingYear"] for r in de_ets}),
        "top_parents": parents.most_common(25),
    }
    print(json.dumps(stats, indent=1, ensure_ascii=False))
    (OUT / "link_stats.json").write_text(json.dumps(stats, indent=1, ensure_ascii=False))

    want = {ets_key(r[col["INSTALLATION_IDENTIFIER"]]) for r in picked}
    fx_ets = [r for r in de_ets if r["ETSIdentifier"] in want]
    fx_inst = [inst[i] for i in dict.fromkeys(r["Installation_INSPIRE_ID"] for r in fx_ets) if i in inst]
    fx_fac = [fac[f] for f in dict.fromkeys(r["Parent_Facility_INSPIRE_ID"] for r in fx_inst) if f in fac]
    write_csv("eea_ets_identifiers.csv", fx_ets)
    write_csv("eea_installations.csv", fx_inst)
    write_csv("eea_facilities.csv", fx_fac)
    print(f"fixtures: {len(fx_ets)} ETS ids, {len(fx_inst)} installations, {len(fx_fac)} facilities")
    for f in fx_fac:
        print("   ", f["Facility_INSPIRE_ID"], "|", f["nameOfFeature"], "|", f["parentCompanyName"], "|", f["city"])


if __name__ == "__main__":
    main()
