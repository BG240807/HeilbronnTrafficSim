"""
SUMO / TraCI bootstrap utilities.

Handles:
    - SUMO binary discovery (sumo-gui vs sumo).
    - Launching the simulator with deterministic seeds.
    - Creating TraCI connections for downstream control loops.
"""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SUMOInitializer:
    """Prepare SUMO configuration and lifecycle."""

    sumo_binary: str = "sumo"
    config_path: Optional[Path] = None
    additional_args: Optional[List[str]] = None
    seed: int = 42

    def build_command(self, gui: bool = False) -> List[str]:
        """Compose the sumo or sumo-gui command line."""
        binary = f"{self.sumo_binary}-gui" if gui else self.sumo_binary
        cmd = [binary, "-S", "-Q", "--seed", str(self.seed)]
        if self.config_path:
            cmd.extend(["-c", str(self.config_path)])
        if self.additional_args:
            cmd.extend(self.additional_args)
        return cmd

    def launch(self, gui: bool = False) -> subprocess.Popen:
        """Launch SUMO and return the process handle."""
        env = os.environ.copy()
        cmd = self.build_command(gui=gui)
        return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)

