"""
Centralized configuration dataclasses.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class SimulationSettings:
    """Top-level knobs for both calibration and sandbox phases."""

    project_root: Path
    sumo_config: Path
    calibration_detectors: List[str]
    scenario_edges: List[str]
    output_dir: Path = field(default_factory=lambda: Path("python_sim/output"))


