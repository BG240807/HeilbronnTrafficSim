"""
Student-focused analytics to quantify disruption.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import pandas as pd


@dataclass
class StudentStressAnalyzer:
    """Track lateness / stress indicators for tagged student agents."""

    student_vehicle_ids: List[str]
    lateness_threshold_minutes: float = 5.0

    def compute_stress_scores(self, arrivals: pd.DataFrame) -> Dict[str, float]:
        """
        arrivals: DataFrame with columns ['agent_id', 'scheduled_arrival', 'actual_arrival'].
        Returns simple stress score (minutes late) per agent.
        """
        scores: Dict[str, float] = {}
        for _, row in arrivals.iterrows():
            delta = (row["actual_arrival"] - row["scheduled_arrival"]).total_seconds() / 60.0
            scores[row["agent_id"]] = max(0.0, delta - self.lateness_threshold_minutes)
        return scores

