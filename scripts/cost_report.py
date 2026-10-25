"""Measured cost per service from the Cloud Billing export, for docs/cost.md and the README.

    python scripts/cost_report.py <project> > cost.md

Net cost = cost + credits (credits are negative), the same figure the budget and the kill switch
use. Reads the standard usage cost export in dataset `billing`; one small query per run.
"""

from __future__ import annotations

import sys

SQL = """
select
  invoice.month as month,
  service.description as service,
  round(sum(cost), 4) as cost,
  round(sum(ifnull((select sum(c.amount) from unnest(credits) as c), 0)), 4) as credits,
  any_value(currency) as currency
from `{project}.billing.gcp_billing_export_v1_*`
where invoice.month >= format_date('%Y%m', date_sub(current_date(), interval 2 month))
group by 1, 2
having cost != 0 or credits != 0
order by 1 desc, 3 desc
"""


def main(project: str) -> None:
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    config = bigquery.QueryJobConfig(maximum_bytes_billed=200 * 1024 * 1024)
    try:
        rows = list(client.query(SQL.format(project=project), job_config=config).result())
    except Exception as error:  # no export table yet: say so instead of failing the run
        print(f"No billing export yet ({type(error).__name__}). Enable it once in the console.")
        return
    print("| month | service | cost | credits | net | currency |")
    print("|---|---|---|---|---|---|")
    totals: dict[str, float] = {}
    for r in rows:
        net = r["cost"] + r["credits"]
        totals[r["month"]] = totals.get(r["month"], 0.0) + net
        print(
            f"| {r['month']} | {r['service']} | {r['cost']:.4f} | {r['credits']:.4f} | {net:.4f} | {r['currency']} |"
        )
    print()
    for month, net in sorted(totals.items(), reverse=True):
        print(f"- {month}: net {net:.4f}")


if __name__ == "__main__":
    main(sys.argv[1])
