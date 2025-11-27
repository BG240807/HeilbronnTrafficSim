"""
Transit punctuality metrics (bus delay tracking).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import pandas as pd


@dataclass
class TransitDelayTracker:
    """Measure deviation from GTFS schedules for bus agents."""

    def summarize(self, trips: pd.DataFrame) -> Dict[str, float]:
        """
        trips: DataFrame with ['trip_id', 'scheduled_departure', 'actual_departure', 'scheduled_arrival', 'actual_arrival'].
        """
        trips["departure_delay_min"] = (trips["actual_departure"] - trips["scheduled_departure"]).dt.total_seconds() / 60
        trips["arrival_delay_min"] = (trips["actual_arrival"] - trips["scheduled_arrival"]).dt.total_seconds() / 60
        return {
            "mean_departure_delay": float(trips["departure_delay_min"].mean()),
            "mean_arrival_delay": float(trips["arrival_delay_min"].mean()),
            "p95_arrival_delay": float(trips["arrival_delay_min"].quantile(0.95)),
        }

