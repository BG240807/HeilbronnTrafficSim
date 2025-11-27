"""
Scenario event hooks for the Heilbronn digital twin.

Focus areas:
    - Construction induced lane closures (Weipertstraße works).
    - Incident injection for stress-testing.
    - Recovery phases for optimization experiments.
"""
from __future__ import annotations

from dataclasses import dataclass

try:
    import traci  # type: ignore
except ImportError:  # pragma: no cover - only needed when running SUMO
    traci = None  # type: ignore


@dataclass
class ConstructionEventManager:
    """Provide helper methods to stage and revert lane closures."""

    target_edge: str
    reduced_lanes: int = 1

    def apply_closure(self, step: int) -> None:
        """Placeholder: use traci.lane.setAllowed / setDisallowed to emulate closures."""
        if not traci:
            raise RuntimeError("TraCI module not available; ensure SUMO_HOME is set.")
        print(f"[ConstructionEventManager] Applying closure at step {step} on edge {self.target_edge}")

    def revert_closure(self, step: int) -> None:
        """Reopen capacity after the simulated works end."""
        if not traci:
            raise RuntimeError("TraCI module not available; ensure SUMO_HOME is set.")
        print(f"[ConstructionEventManager] Reverting closure at step {step} on edge {self.target_edge}")
