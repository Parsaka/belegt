"""Decision logic of the billing kill switch (infra/functions/kill_switch/main.py)."""

import base64
import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest
from functions_framework import _function_registry

PATH = Path(__file__).resolve().parents[1] / "infra" / "functions" / "kill_switch" / "main.py"
spec = importlib.util.spec_from_file_location("kill_switch", PATH)
assert spec and spec.loader
kill_switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kill_switch)


def test_registered_as_a_cloud_event_function():
    # Regression: undecorated, production called it with (data, context) and raised TypeError.
    assert _function_registry.get_func_signature_type("stop_billing", None) == "cloudevent"


@pytest.mark.parametrize(
    ("cost", "budget", "fraction", "expected"),
    [
        (0.00, 1.00, 0.6, False),
        (0.59, 1.00, 0.6, False),
        (0.60, 1.00, 0.6, True),
        (2.00, 1.00, 0.6, True),
        (1.20, 1.50, 0.8, True),  # float trap: 1.5 * 0.8 != 1.2
        (5.00, 0.00, 0.8, False),  # a zero budget must never detach billing by accident
    ],
)
def test_should_disable(cost, budget, fraction, expected):
    assert kill_switch.should_disable(cost, budget, fraction) is expected


def test_parse_budget_notification():
    payload = {"costAmount": 1.23, "budgetAmount": 1.5, "currencyCode": "EUR"}
    assert kill_switch.parse_notification(json.dumps(payload).encode()) == (1.23, 1.5, False)


@pytest.mark.parametrize(("flag", "drill"), [(True, True), ("true", False), (1, False)])
def test_only_an_explicit_drill_flag_counts(flag, drill):
    payload = {"costAmount": 1, "budgetAmount": 1, "belegtDrill": flag}
    assert kill_switch.parse_notification(json.dumps(payload).encode())[2] is drill


class _Event:
    def __init__(self, cost: float, budget: float, drill: bool = False) -> None:
        payload: dict[str, object] = {"costAmount": cost, "budgetAmount": budget}
        if drill:
            payload["belegtDrill"] = True
        raw = base64.b64encode(json.dumps(payload).encode())
        self.data = {"message": {"data": raw}}


class _Billing:
    """Stands in for google.cloud.billing_v1 and records what the function did."""

    def __init__(self, granted: list[str]) -> None:
        self.granted = granted
        self.detached: list[str] = []
        billing = self

        class Client:
            def get_project_billing_info(self, name):
                return types.SimpleNamespace(
                    billing_enabled=True, billing_account_name="billingAccounts/X"
                )

            def test_iam_permissions(self, resource, permissions):
                return types.SimpleNamespace(
                    permissions=[p for p in permissions if p in billing.granted]
                )

            def update_project_billing_info(self, name, project_billing_info):
                billing.detached.append(name)

        self.CloudBillingClient = Client
        self.ProjectBillingInfo = lambda billing_account_name: billing_account_name


@pytest.fixture
def billing(monkeypatch):
    def install(granted):
        fake = _Billing(granted)
        cloud = types.ModuleType("google.cloud")
        cloud.billing_v1 = fake
        monkeypatch.setitem(sys.modules, "google.cloud", cloud)
        monkeypatch.setitem(sys.modules, "google.cloud.billing_v1", fake)
        monkeypatch.setenv("GCP_PROJECT_ID", "p")
        monkeypatch.setenv("KILL_SWITCH_FRACTION", "0.6")
        return fake

    return install


def test_drill_checks_the_permission_and_never_detaches(billing, capsys):
    fake = billing([kill_switch.DETACH_PERMISSION])
    kill_switch.stop_billing(_Event(cost=5, budget=1, drill=True))
    assert fake.detached == []
    assert "drill: WOULD DETACH billing from p" in capsys.readouterr().out


def test_drill_reports_a_missing_permission(billing, capsys):
    fake = billing([])
    kill_switch.stop_billing(_Event(cost=5, budget=1, drill=True))
    assert fake.detached == []
    assert "CANNOT DETACH" in capsys.readouterr().out


def test_real_notification_over_threshold_detaches(billing):
    fake = billing([kill_switch.DETACH_PERMISSION])
    kill_switch.stop_billing(_Event(cost=0.6, budget=1))
    assert fake.detached == ["projects/p"]


def test_below_threshold_does_not_touch_billing(monkeypatch, capsys):
    monkeypatch.setenv("GCP_PROJECT_ID", "p")
    monkeypatch.setenv("KILL_SWITCH_FRACTION", "0.8")
    # Would raise ImportError if it reached the billing client, which is not installed in CI.
    kill_switch.stop_billing(_Event(cost=0.4, budget=1.5))
    assert '"cost": 0.4' in capsys.readouterr().out
