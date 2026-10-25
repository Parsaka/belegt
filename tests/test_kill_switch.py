"""Decision logic of the billing kill switch (infra/functions/kill_switch/main.py)."""

import base64
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1] / "infra" / "functions" / "kill_switch" / "main.py"
spec = importlib.util.spec_from_file_location("kill_switch", PATH)
assert spec and spec.loader
kill_switch = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kill_switch)


@pytest.mark.parametrize(
    ("cost", "budget", "fraction", "expected"),
    [
        (0.00, 1.50, 0.8, False),
        (1.19, 1.50, 0.8, False),
        (1.20, 1.50, 0.8, True),
        (2.00, 1.50, 0.8, True),
        (5.00, 0.00, 0.8, False),  # a zero budget must never detach billing by accident
    ],
)
def test_should_disable(cost, budget, fraction, expected):
    assert kill_switch.should_disable(cost, budget, fraction) is expected


def test_parse_budget_notification():
    payload = {"costAmount": 1.23, "budgetAmount": 1.5, "currencyCode": "EUR"}
    assert kill_switch.parse_notification(json.dumps(payload).encode()) == (1.23, 1.5)


class _Event:
    def __init__(self, cost: float, budget: float) -> None:
        raw = base64.b64encode(json.dumps({"costAmount": cost, "budgetAmount": budget}).encode())
        self.data = {"message": {"data": raw}}


def test_below_threshold_does_not_touch_billing(monkeypatch, capsys):
    monkeypatch.setenv("GCP_PROJECT_ID", "p")
    monkeypatch.setenv("KILL_SWITCH_FRACTION", "0.8")
    # Would raise ImportError if it reached the billing client, which is not installed in CI.
    kill_switch.stop_billing(_Event(cost=0.4, budget=1.5))
    assert '"cost": 0.4' in capsys.readouterr().out
