"""
Economic impact conversions (time lost -> Euros).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EconomicImpactCalculator:
    """Translate aggregate delay into monetary loss."""

    hourly_value_eur: float

    def compute_loss(self, hours_lost: float) -> float:
        """Simple proportional conversion."""
        return hours_lost * self.hourly_value_eur

