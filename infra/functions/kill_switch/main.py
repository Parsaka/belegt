"""Detach billing from the project once spend reaches the kill-switch threshold.

Follows https://docs.cloud.google.com/billing/docs/how-to/disable-billing-with-notifications.
Detaching billing stops every service in the project, including free-tier ones. Everything is
Terraform, so `terraform apply` after re-linking billing restores it.
"""

from __future__ import annotations

import base64
import json
import os
from decimal import Decimal
from typing import Any


def should_disable(cost: float, budget: float, fraction: float) -> bool:
    """Fire at `fraction` of the budget, below 100 %, because cost data arrives late."""
    if budget <= 0:
        return False
    # Decimal, because 1.5 * 0.8 is 1.2000000000000002 in floating point and 1.20 would not fire.
    return Decimal(str(cost)) >= Decimal(str(budget)) * Decimal(str(fraction))


# Permission the detach needs on the billing account (part of Billing Account Administrator).
DETACH_PERMISSION = "billing.resourceAssociations.delete"


def parse_notification(data: bytes) -> tuple[float, float, bool]:
    """Cost, budget, and whether this is a drill. Budget messages never carry `belegtDrill`;
    only the kill-switch test workflow sends it."""
    payload = json.loads(data.decode("utf-8"))
    return (
        float(payload["costAmount"]),
        float(payload["budgetAmount"]),
        payload.get("belegtDrill") is True,
    )


def stop_billing(cloud_event: Any) -> None:
    raw = cloud_event.data["message"]["data"]
    cost, budget, drill = parse_notification(base64.b64decode(raw))
    fraction = float(os.environ.get("KILL_SWITCH_FRACTION", "0.8"))
    project_id = os.environ["GCP_PROJECT_ID"]
    decision = should_disable(cost, budget, fraction)
    print(json.dumps({"cost": cost, "budget": budget, "fraction": fraction, "drill": drill}))

    if not decision:
        return

    # Imported lazily so the decision logic above can be tested without the client library.
    from google.cloud import billing_v1

    client = billing_v1.CloudBillingClient()
    name = f"projects/{project_id}"
    info = client.get_project_billing_info(name=name)
    if not info.billing_enabled:
        print("billing already disabled")
        return
    if drill:
        # Everything up to the detach: the decision, the identity, reading billing, and the
        # permission the detach needs. A real detach is a separate, owner-approved test.
        granted = client.test_iam_permissions(
            resource=info.billing_account_name, permissions=[DETACH_PERMISSION]
        ).permissions
        verdict = "WOULD DETACH" if DETACH_PERMISSION in granted else "CANNOT DETACH"
        print(f"drill: {verdict} billing from {project_id} ({info.billing_account_name})")
        return
    client.update_project_billing_info(
        name=name, project_billing_info=billing_v1.ProjectBillingInfo(billing_account_name="")
    )
    print(f"billing detached from {project_id}")
