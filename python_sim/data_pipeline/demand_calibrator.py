"""
Demand calibration utilities that align simulated volumes with ground truth.

The core idea is to use the ingested detector counts and iteratively adjust OD
matrices / departure rates until simulated counts fall within tolerance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

import numpy as np
import pandas as pd


@dataclass
class DemandCalibrator:
    """Calibrate demand for SUMO using detector counts + optimization routines."""

    target_counts: pd.DataFrame
    tolerance: float = 0.05

    def score_run(self, simulated_counts: pd.DataFrame) -> Dict[str, float]:
        """Compute RMSE and MAPE vs. observed detectors."""
        diff = simulated_counts - self.target_counts.loc[simulated_counts.index]
        rmse = np.sqrt((diff ** 2).mean()).mean()
        mape = (diff.abs() / self.target_counts).replace([np.inf, np.nan], 0).mean().mean()
        return {"rmse": float(rmse), "mape": float(mape)}

    def needs_recalibration(self, metrics: Dict[str, float]) -> bool:
        """Decide whether another calibration iteration is required."""
        return metrics["mape"] > self.tolerance

