"""
Calibration validation utilities (e.g., Fundamental Diagrams).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import pandas as pd


@dataclass
class FundamentalDiagramValidator:
    """Produces Flow vs Density plots to verify microscopic realism."""

    output_dir: Path

    def plot(self, aggregation: pd.DataFrame, detector_id: str) -> Path:
        """Generate and persist a fundamental diagram for a detector."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        fig, ax = plt.subplots()
        ax.scatter(aggregation["density"], aggregation["flow"], s=8, alpha=0.6)
        ax.set_xlabel("Density [veh/km]")
        ax.set_ylabel("Flow [veh/h]")
        ax.set_title(f"Fundamental Diagram - {detector_id}")
        target = self.output_dir / f"fd_{detector_id}.png"
        fig.savefig(target, dpi=200, bbox_inches="tight")
        plt.close(fig)
        return target

