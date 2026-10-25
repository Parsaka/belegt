"""Discover and describe the raw source files (run in GitHub Actions, which has network access).

Prints what each publisher actually serves: file links, sheet names, header rows, row counts.
Writes trimmed samples to `inspect/` so they can become test fixtures.
"""

from __future__ import annotations

import io
import json
import re
import sys
import zipfile
from pathlib import Path
from urllib.parse import urljoin

import httpx
from openpyxl import load_workbook

UA = {"User-Agent": "belegt-portfolio/0.1 (+https://github.com/Parsaka/belegt)"}
OUT = Path("inspect")
OUT.mkdir(exist_ok=True)
client = httpx.Client(headers=UA, timeout=120, follow_redirects=True)


def section(title: str) -> None:
    print(f"\n{'=' * 20} {title} {'=' * 20}", flush=True)


def describe_xlsx(name: str, content: bytes) -> None:
    wb = load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    for ws in wb.worksheets:
        rows = list(ws.iter_rows(values_only=True))
        print(f"-- sheet {ws.title!r}: {len(rows)} rows")
        for i, row in enumerate(rows[:25]):
            print(f"   {i:>3}: {row}")
        sample = [list(r) for r in rows[:60]]
        (OUT / f"{name}__{ws.title}.json").write_text(json.dumps(sample, default=str))


def union_registry() -> None:
    section("EU ETS Union Registry")
    page = "https://climate.ec.europa.eu/areas-action/carbon-markets/eu-emissions-trading-system-eu-ets/union-registry_en"
    html = client.get(page).text
    links = sorted(set(re.findall(r'href="([^"]+\.(?:xlsx|xls)[^"]*)"', html)))
    links += sorted(set(re.findall(r'href="([^"]*/document/download/[^"]+)"', html)))
    for link in links:
        print("link:", urljoin(page, link))
    wanted = ("verified_emissions_2025_en.xlsx", "compliance_2025_code_en.xlsx")
    for link in dict.fromkeys(links):
        url = urljoin(page, link)
        if not url.endswith(wanted):
            continue
        r = client.get(url)
        print(f"\nGET {url} -> {r.status_code} {len(r.content)} bytes")
        wb = load_workbook(io.BytesIO(r.content), read_only=True, data_only=True)
        for ws in wb.worksheets:
            rows = list(ws.iter_rows(values_only=True))
            hdr_i = next(
                (i for i, row in enumerate(rows) if row and row[0] == "REGISTRY_CODE"), None
            )
            if hdr_i is None:
                continue
            hdr = rows[hdr_i]
            print(
                f"-- sheet {ws.title!r}: header at row {hdr_i}, {len(rows) - hdr_i - 1} data rows"
            )
            print("   header:", hdr)
            body = [r_ for r_ in rows[hdr_i + 1 :] if r_ and r_[0]]
            if "ACCOUNT_TYPE" in hdr:
                at = hdr.index("ACCOUNT_TYPE")
                counts: dict[str, int] = {}
                for r_ in body:
                    counts[str(r_[at])] = counts.get(str(r_[at]), 0) + 1
                print("   account types:", counts)
            de = [r_ for r_ in body if r_[0] == "DE"]
            print(f"   DE rows: {len(de)}")
            stationary = [
                r_ for r_ in de if str(r_[-1]).upper() == "OPERATOR HOLDING ACCOUNT"
            ] or de
            sample = [list(hdr)] + [list(r_) for r_ in stationary[:40]]
            name = url.split("filename=")[-1].removesuffix(".xlsx")
            (OUT / f"{name}__{ws.title}__de_sample.json").write_text(
                json.dumps(sample, default=str)
            )
            for r_ in stationary[:8]:
                print("   ", r_[:14])


def union_registry_site() -> None:
    section("union-registry-data.ec.europa.eu")
    for url in [
        "https://union-registry-data.ec.europa.eu/",
        "https://union-registry-data.ec.europa.eu/report/welcome",
    ]:
        r = client.get(url)
        print(url, r.status_code, r.headers.get("content-type"))
        print(r.text[:1500])


def eea() -> None:
    section("EEA Industrial Reporting")
    r = client.get("https://sdi.eea.europa.eu/webdav/datastore/public/")
    print("datastore final url:", r.url, r.status_code)
    m = re.search(r"/s/([A-Za-z0-9]+)", str(r.url)) or re.search(
        r'sharingToken"\s*value="([^"]+)"', r.text
    )
    token = m.group(1) if m else None
    print("share token:", token)
    if token:
        dav = "https://sdi.eea.europa.eu/datashare/public.php/webdav/"

        def ls(path: str) -> list[str]:
            pr = client.request("PROPFIND", dav + path, auth=(token, ""), headers={"Depth": "1"})
            hrefs = re.findall(r"<d:href>([^<]+)</d:href>", pr.text)
            return [h.split("/public.php/webdav/", 1)[1] for h in hrefs]

        root = [h for h in ls("") if "eprtr" in h.lower()]
        print("eprtr folders:", root)

        def ver(h: str) -> int:
            m = re.search(r"_v(\d+)_", h)
            return int(m.group(1)) if m else -1

        latest = max(root, key=ver)
        print("latest:", latest)
        for h in ls(latest):
            print("   ", h)
        csv_entry = next(h for h in ls(latest) if "csv" in h.lower() and h != latest)
        for h in ls(csv_entry) if csv_entry.endswith("/") else [csv_entry]:
            print("    csv:", h)
            if h.endswith("/"):
                continue
            r2 = client.get(dav + h, auth=(token, ""))
            print("      GET", r2.status_code, len(r2.content))
            blobs: list[tuple[str, bytes]] = []
            if r2.content[:2] == b"PK":
                with zipfile.ZipFile(io.BytesIO(r2.content)) as z:
                    for info in z.infolist():
                        with z.open(info) as fh:
                            blobs.append((info.filename, fh.read()))
            else:
                blobs.append((h.rsplit("/", 1)[-1], r2.content))
            for fname, blob in blobs:
                text = blob.decode("utf-8-sig", "replace")
                lines = text.splitlines()
                print(f"      {fname}: {len(lines)} lines")
                for line in lines[:4]:
                    print("         ", line[:700])
                de = [ln for ln in lines[1:] if re.search(r'(^|[;,"])DE([;,"]|$)', ln)][:40]
                print(f"         DE-looking rows (first 40 kept): {len(de)}")
                safe = re.sub(r"[^A-Za-z0-9_.-]", "_", Path(fname).name)
                (OUT / f"eea__{safe}").write_text("\n".join([lines[0], *de]))
    q = {
        "query": {"query_string": {"query": "Industrial Reporting IED E-PRTR tabular"}},
        "size": 10,
        "_source": ["resourceTitleObject", "uuid", "resourceTemporalDateRange", "createDate"],
    }
    sr = client.post(
        "https://sdi.eea.europa.eu/catalogue/srv/api/search/records/_search",
        json=q,
        headers={"Accept": "application/json"},
    )
    print("catalogue search", sr.status_code)
    for hit in sr.json().get("hits", {}).get("hits", []) if sr.status_code == 200 else []:
        src = hit.get("_source", {})
        print("   ", src.get("uuid"), (src.get("resourceTitleObject") or {}).get("default"))
    return
    base = "https://sdi.eea.europa.eu/webdav/datastore/public/"
    html = client.get(base).text
    dirs = sorted(set(re.findall(r'href="[^"]*?(eea_t_ied-eprtr[^"/]*)/?"', html)))
    print("datasets:", dirs)
    if not dirs:
        print(html[:2000])
        return

    def version(d: str) -> int:
        m = re.search(r"_v(\d+)_", d)
        return int(m.group(1)) if m else -1

    latest = max(dirs, key=version)
    print("latest:", latest)
    listing = client.get(base + latest + "/").text
    files = re.findall(r'href="([^"?]+)"', listing)
    for f in files:
        print("  file:", f)
    for f in files:
        if f.lower().endswith(".zip") and ("csv" in f.lower() or "user" in f.lower()):
            url = urljoin(base + latest + "/", f)
            r = client.get(url)
            print(f"GET {url} -> {r.status_code} {len(r.content)} bytes")
            with zipfile.ZipFile(io.BytesIO(r.content)) as z:
                for info in z.infolist():
                    print(f"   {info.filename} {info.file_size}")
                    if info.filename.lower().endswith(".csv"):
                        with z.open(info) as fh:
                            head = fh.read(4000).decode("utf-8", "replace").splitlines()[:6]
                        for line in head:
                            print("      ", line[:400])
                        (OUT / Path(info.filename).name).write_text("\n".join(head))


def gleif() -> None:
    section("GLEIF")
    r = client.get(
        "https://api.gleif.org/api/v1/lei-records",
        params={"filter[entity.legalName]": "BASF SE", "page[size]": 1},
    )
    print("lei search", r.status_code)
    data = r.json()
    print(json.dumps(data, indent=1)[:3000])
    if data.get("data"):
        lei = data["data"][0]["id"]
        for rel in ("direct-parent", "ultimate-parent", "direct-children"):
            rr = client.get(
                f"https://api.gleif.org/api/v1/lei-records/{lei}/{rel}", params={"page[size]": 3}
            )
            print(rel, rr.status_code, rr.text[:800])
    gc = client.get("https://goldencopy.gleif.org/api/v2/golden-copies/publishes/latest")
    print("golden copy latest", gc.status_code)
    data = gc.json()["data"]
    for kind in ("lei2", "rr", "repex"):
        full = data.get(kind, {}).get("full_file", {}).get("csv", {})
        print(
            f"   {kind}: {full.get('record_count')} records, {full.get('size_human_readable')}, {full.get('url')}"
        )
    rr_url = data["rr"]["full_file"]["csv"]["url"]
    rr = client.get(rr_url)
    with zipfile.ZipFile(io.BytesIO(rr.content)) as z:
        name = z.namelist()[0]
        with z.open(name) as fh:
            head = [fh.readline().decode() for _ in range(6)]
    for line in head:
        print("   RR:", line.strip()[:600])
    (OUT / "gleif_rr_head.csv").write_text("".join(head))
    # Small real fixtures: a few German groups and their direct children
    for name in ("BASF SE", "Heidelberg Materials AG", "RWE Aktiengesellschaft"):
        r = client.get(
            "https://api.gleif.org/api/v1/lei-records",
            params={"filter[entity.legalName]": name, "page[size]": 1},
        )
        rec = r.json().get("data", [])
        if not rec:
            print("   no LEI for", name)
            continue
        lei = rec[0]["id"]
        kids = client.get(
            f"https://api.gleif.org/api/v1/lei-records/{lei}/direct-children",
            params={"page[size]": 20},
        ).json()
        print(
            f"   {name}: {lei}, direct children total {kids.get('meta', {}).get('pagination', {}).get('total')}"
        )
        safe = re.sub(r"[^A-Za-z0-9]", "_", name)
        (OUT / f"gleif__{safe}.json").write_text(
            json.dumps({"parent": rec[0], "children": kids.get("data", [])})
        )


if __name__ == "__main__":
    steps = {"ur": union_registry, "ursite": union_registry_site, "eea": eea, "gleif": gleif}
    for key in sys.argv[1:] or steps:
        try:
            steps[key]()
        except Exception as exc:  # discovery script: keep going
            print(f"!! {key} failed: {exc!r}")
