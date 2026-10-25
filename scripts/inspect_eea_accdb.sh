#!/usr/bin/env bash
# Lists the tables of the EEA Industrial Reporting Access database and prints the columns and
# German sample rows of the tables that link facilities to EU ETS ids and parent companies.
set -euo pipefail
mkdir -p inspect/accdb
TOKEN=sptXqwkQr5g7Bp5
DAV=https://sdi.eea.europa.eu/datashare/public.php/webdav/eea_t_ied-eprtr_p_2007-2024_v16_r00
curl -sS -u "$TOKEN:" -o /tmp/eea.accdb "$DAV/Industrial_dataset_v_16_2026_02_16.accdb"
ls -l /tmp/eea.accdb
mdb-ver /tmp/eea.accdb || true
mdb-tables -1 /tmp/eea.accdb | tee inspect/accdb/tables.txt
while read -r t; do
  [ -z "$t" ] && continue
  rows=$(mdb-export /tmp/eea.accdb "$t" 2>/dev/null | wc -l || true)
  echo "== $t ($rows lines)"
  mdb-export /tmp/eea.accdb "$t" | head -3 | cut -c1-600
  case "$t" in
    *ETS*|*ProductionFacility*|*Facility*|*Installation*|*Parent*|*Site*)
      safe=$(echo "$t" | tr -c 'A-Za-z0-9_\n' '_')
      { mdb-export /tmp/eea.accdb "$t" | head -1; mdb-export /tmp/eea.accdb "$t" | grep -E '(^|,)"?DE' | head -60; } > "inspect/accdb/${safe}.csv" || true
      ;;
  esac
done < inspect/accdb/tables.txt
