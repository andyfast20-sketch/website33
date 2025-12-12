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
