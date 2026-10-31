"""Print a Markdown summary of a pipeline run: dbt results, bytes processed and measured numbers.

    python scripts/run_summary.py duckdb data/belegt.duckdb dbt/target
    python scripts/run_summary.py bigquery <project-id> dbt/target

The pipeline pushes this to the ops-results branch. Docs and the README quote numbers from it,
never estimates.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

QUERIES = {
    "Rows per mart": """
        select 'dim_installation' as model, count(*) as n from {m}.dim_installation
        union all select 'fct_verified_emissions', count(*) from {m}.fct_verified_emissions
        union all select 'dim_legal_entity', count(*) from {m}.dim_legal_entity
        union all select 'bridge_ownership', count(*) from {m}.bridge_ownership
        union all select 'mart_group_emissions', count(*) from {m}.mart_group_emissions
        union all select 'review_entity_matches', count(*) from {m}.review_entity_matches
    """,
    "Accounts by kind": """
        select installation_kind, count(*) as accounts,
               sum(case when match_decision = 'accepted' then 1 else 0 end) as accepted
        from {m}.dim_installation group by 1 order by 2 desc
    """,
    "Installations by match decision and path": """
        select coalesce(match_decision, 'no candidate') as decision, match_path,
               count(*) as installations
        from {m}.dim_installation group by 1, 2 order by 3 desc
    """,
    "Installations with a map point, by source": """
        select coalesce(location_source, 'no point') as source, count(*) as installations
        from {m}.dim_installation
        where installation_kind = 'stationary installation'
        group by 1 order by 2 desc
    """,
    "Verified tonnes attributed to a company, by year (last five)": """
        select f.reporting_year,
               sum(f.verified_t) as verified_t,
               sum(case when d.match_decision = 'accepted' then f.verified_t end) as attributed_t
        from {m}.fct_verified_emissions as f
        join {m}.dim_installation as d using (ets_identifier)
        where f.is_reported
        group by 1 order by 1 desc limit 5
    """,
    "Largest groups in the latest year": """
        select group_name, group_lei, reporting_year, verified_t, installations
        from {m}.mart_group_emissions
        where reporting_year = (select max(reporting_year) from {m}.mart_group_emissions)
        order by verified_t desc limit 15
    """,
}


HEADERS = {
    "Rows per mart": ["model", "rows"],
    "Accounts by kind": ["kind", "accounts", "matched to a company"],
    "Installations by match decision and path": ["decision", "path", "installations"],
    "Installations with a map point, by source": ["source", "stationary installations"],
    "Verified tonnes attributed to a company, by year (last five)": [
        "year",
        "verified t",
        "attributed t",
    ],
    "Largest groups in the latest year": ["group", "LEI", "year", "verified t", "installations"],
}


def table(rows: list[tuple[Any, ...]], header: list[str]) -> str:
    def cell(v: Any) -> str:
        return f"{v:,}" if isinstance(v, int) and abs(v) >= 10_000 else str(v)

    lines = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    lines += ["| " + " | ".join(cell(v) for v in r) + " |" for r in rows]
    return "\n".join(lines)


def dbt_results(target: Path) -> str:
    path = target / "run_results.json"
    if not path.exists():
        return "_no run_results.json_"
    results = json.loads(path.read_text())["results"]
    rows = []
    total_bytes = 0
    for r in results:
        resp = r.get("adapter_response") or {}
        processed = resp.get("bytes_processed")
        total_bytes += processed or 0
        rows.append(
            (
                r["unique_id"].split(".", 2)[-1],
                r["status"],
                round(r.get("execution_time") or 0, 1),
                "" if processed is None else processed,
            )
        )
    failed = [r for r in rows if r[1] not in ("success", "pass")]
    out = [
        f"{len(rows)} nodes, {len(failed)} not passing, {total_bytes:,} bytes processed in total",
        "",
        table(failed, ["node", "status", "seconds", "bytes processed"])
        if failed
        else "All nodes passed.",
        "",
        "<details><summary>All nodes</summary>\n",
        table(rows, ["node", "status", "seconds", "bytes processed"]),
        "\n</details>",
    ]
    return "\n".join(out)


def runner(backend: str, where: str) -> tuple[Callable[[str], list[tuple[Any, ...]]], str]:
    if backend == "duckdb":
        import duckdb

        con = duckdb.connect(where, read_only=True)

        def run_duckdb(sql: str) -> list[tuple[Any, ...]]:
            return [tuple(r) for r in con.execute(sql).fetchall()]

        return run_duckdb, "marts"
    from google.cloud import bigquery

    client = bigquery.Client(project=where)

    def run_bigquery(sql: str) -> list[tuple[Any, ...]]:
        job = client.query(sql)
        return [tuple(r.values()) for r in job.result()]

    return run_bigquery, f"`{where}.marts`"


def main(backend: str, where: str, target: str) -> None:
    print(f"# Pipeline summary ({backend})\n")
    print("## dbt build\n")
    print(dbt_results(Path(target)))
    run, marts = runner(backend, where)
    for title, sql in QUERIES.items():
        print(f"\n## {title}\n")
        try:
            rows = run(sql.format(m=marts))
        except Exception as exc:  # a summary must not hide the rest of the report
            print(f"_query failed: {exc}_")
            continue
        print(table(rows, HEADERS[title]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
