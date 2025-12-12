import math

import pytest

from agent.billing import BillingConfig, build_billing_view, build_call_charges, calculate_charge


def test_calculate_charge_rounds_up_and_adds_connection_fee():
    config = BillingConfig(per_minute_rate=0.10, connection_fee=0.25, rounding_increment_seconds=30)
    # 45s rounds to 60s (1 minute)
    assert calculate_charge(45, config) == 0.35
    # 95s rounds to 120s (2 minutes)
    assert calculate_charge(95, config) == 0.45


def test_calculate_charge_rejects_negative_duration():
    config = BillingConfig(per_minute_rate=0.10)
    with pytest.raises(ValueError):
        calculate_charge(-1, config)


def test_build_call_charges_uses_settings_defaults(monkeypatch):
    monkeypatch.setattr(
        "agent.config.settings.vonage_per_minute_charge", 0.20,
    )
    monkeypatch.setattr(
        "agent.config.settings.vonage_connection_charge", 0.50,
    )
    monkeypatch.setattr(
        "agent.config.settings.vonage_rounding_increment_seconds", 60,
    )

    records = [
        {"id": "call-1", "duration_seconds": 60, "caller": "+15551234567"},
        {"id": "call-2", "duration_seconds": 130},
    ]

    rows = build_call_charges(records)
    assert [row.call_id for row in rows] == ["call-1", "call-2"]
    assert rows[0].charge == pytest.approx(0.70)
    # 130 seconds -> 180 rounded (3 minutes)
    assert rows[1].charge == pytest.approx(1.10)
    assert rows[0].caller == "+15551234567"
    assert rows[1].caller is None


def test_build_call_charges_validates_records():
    config = BillingConfig(per_minute_rate=0.10)
    with pytest.raises(ValueError):
        build_call_charges([{"duration_seconds": "not-an-int"}], config)


def test_build_billing_view_shapes_data_for_ui():
    config = BillingConfig(per_minute_rate=0.05, connection_fee=0.01, rounding_increment_seconds=60)
    records = [
        {"id": "call-1", "duration_seconds": 60, "caller": "Alice"},
        {"id": "call-2", "duration_seconds": 90, "caller": "Bob"},
        {"id": "call-3", "duration_seconds": 20, "caller": "Carol"},
    ]

    view = build_billing_view(
        records,
        current_balance=57.0,
        total_used=3.47,
        config=config,
    )

    assert view["header"] == "💰 Billing & Usage"
    assert view["summary"] == {"current_balance": 57.0, "total_used": 3.47}
    assert [card["label"] for card in view["pricing_cards"]] == ["Calls", "Minutes", "Bookings"]

    history = view["usage_history"]
    assert len(history) == 3
    assert history[0]["charge"] == pytest.approx(0.06)
    assert history[1]["charge"] == pytest.approx(0.11)
    assert history[2]["charge"] == pytest.approx(0.06)


def test_build_billing_view_calculates_total_used_when_missing():
    config = BillingConfig(per_minute_rate=0.10)
    records = [{"id": "call-1", "duration_seconds": 60}]

    view = build_billing_view(records, current_balance=10.0, total_used=None, config=config)

    assert view["summary"]["total_used"] == pytest.approx(0.10)
