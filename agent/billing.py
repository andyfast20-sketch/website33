"""Billing helpers for summarizing per-call charges.

The functions here calculate charges based on rates configured in
environment variables that mirror the values set on the Vonage Agent
Server control page. They can be used by a UI layer to present the
"billing screen" for individual accounts without duplicating the
business logic in the frontend.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .config import settings


@dataclass
class BillingConfig:
    """Configuration used to price calls."""

    per_minute_rate: float
    connection_fee: float = 0.0
    rounding_increment_seconds: int = 60

    @classmethod
    def from_settings(cls, *, per_minute_rate: Optional[float] = None,
                      connection_fee: Optional[float] = None,
                      rounding_increment_seconds: Optional[int] = None) -> "BillingConfig":
        """Create a config using `settings` defaults with optional overrides."""

        return cls(
            per_minute_rate=per_minute_rate if per_minute_rate is not None else settings.vonage_per_minute_charge,
            connection_fee=connection_fee if connection_fee is not None else settings.vonage_connection_charge,
            rounding_increment_seconds=rounding_increment_seconds if rounding_increment_seconds is not None else settings.vonage_rounding_increment_seconds,
        )


@dataclass
class CallCharge:
    """Represents a single call and its computed charge."""

    call_id: str
    duration_seconds: int
    charge: float
    caller: Optional[str] = None

    @property
    def duration_minutes(self) -> float:
        return round(self.duration_seconds / 60, 2)


def build_billing_view(
    records: Iterable[dict],
    *,
    current_balance: float,
    total_used: Optional[float] = None,
    config: Optional[BillingConfig] = None,
) -> dict:
    """Assemble a serializable payload for a billing screen.

    The view model keeps UI rendering simple while ensuring the values on the
    page align with the shared pricing logic in :func:`build_call_charges`.
    """

    billing_config = config or BillingConfig.from_settings()
    call_charges = build_call_charges(records, billing_config)
    computed_total_used = sum(charge.charge for charge in call_charges)
    total_duration_seconds = sum(charge.duration_seconds for charge in call_charges)

    return {
        "header": "💰 Billing & Usage",
        "summary": {
            "current_balance": current_balance,
            "total_used": total_used if total_used is not None else round(computed_total_used, 2),
        },
        "usage_totals": {
            "call_count": len(call_charges),
            "total_duration_seconds": total_duration_seconds,
            "total_duration_minutes": round(total_duration_seconds / 60, 2),
            "total_charges": round(computed_total_used, 2),
        },
        "pricing_cards": [
            {
                "label": "Calls",
                "value": f"Connection fee {billing_config.connection_fee:.2f} credits",
            },
            {
                "label": "Minutes",
                "value": f"{billing_config.per_minute_rate:.2f} credits per minute",
            },
            {
                "label": "Bookings",
                "value": f"Rounded every {billing_config.rounding_increment_seconds} seconds",
            },
        ],
        "usage_history": [
            {
                "call_id": charge.call_id,
                "caller": charge.caller,
                "duration_seconds": charge.duration_seconds,
                "duration_minutes": charge.duration_minutes,
                "charge": charge.charge,
            }
            for charge in call_charges
        ],
    }


def build_account_billing_pages(
    accounts: Iterable[dict], *, config: Optional[BillingConfig] = None
) -> dict:
    """Return a consolidated billing view for multiple accounts.

    Each entry in ``accounts`` should provide:

    - ``account_id``: unique identifier for the account
    - ``records``: iterable of call dictionaries with ``duration_seconds`` and optional
      ``id``/``caller``
    - ``current_balance``: remaining credits for the account
    - ``total_used``: optional override for total credits consumed

    The helper keeps billing concerns isolated from presentation logic while
    ensuring that calls are never cross-contaminated between accounts.
    """

    billing_config = config or BillingConfig.from_settings()

    pages = []
    seen_accounts = set()

    for account in accounts:
        account_id = account.get("account_id")
        if not account_id:
            raise ValueError("Each account entry requires an 'account_id'")
        if account_id in seen_accounts:
            raise ValueError(f"Duplicate account_id detected: {account_id}")

        seen_accounts.add(account_id)
        view = build_billing_view(
            account.get("records", []),
            current_balance=account.get("current_balance", 0.0),
            total_used=account.get("total_used"),
            config=billing_config,
        )

        # Make it clear to UIs which account a block belongs to without forcing
        # them to re-label headers or introspect nested data.
        view["account_id"] = account_id
        pages.append(view)

    return {"accounts": pages, "header": "💰 Billing & Usage"}


def calculate_charge(duration_seconds: int, config: BillingConfig) -> float:
    """Calculate the billable charge for a call duration.

    Durations are rounded up to the nearest increment (defaults to 60s) so
    that frontend renderers can display the same totals the backend uses.
    """

    if duration_seconds < 0:
        raise ValueError("duration_seconds must be non-negative")

    rounded_seconds = max(
        config.rounding_increment_seconds,
        math.ceil(duration_seconds / config.rounding_increment_seconds) * config.rounding_increment_seconds,
    )
    minutes = rounded_seconds / 60
    return round(config.connection_fee + minutes * config.per_minute_rate, 2)


def build_call_charges(records: Iterable[dict], config: Optional[BillingConfig] = None) -> List[CallCharge]:
    """Return `CallCharge` rows for UI consumption.

    Each `record` should contain ``id`` and ``duration_seconds`` keys and
    may optionally include ``caller``. This keeps the "billing screen"
    rendering layer simple: it just needs to iterate the returned rows to
    show per-call charges that align with the Vonage control page rates.
    """

    billing_config = config or BillingConfig.from_settings()
    call_charges: List[CallCharge] = []
    for record in records:
        try:
            duration = int(record["duration_seconds"])
        except (KeyError, TypeError, ValueError) as exc:  # pragma: no cover - defensive guard
            raise ValueError("Each record requires an integer 'duration_seconds' field") from exc

        call_charges.append(
            CallCharge(
                call_id=str(record.get("id", "")),
                duration_seconds=duration,
                charge=calculate_charge(duration, billing_config),
                caller=record.get("caller"),
            )
        )
    return call_charges
