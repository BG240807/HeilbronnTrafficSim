"""
Main orchestration entry point for the Heilbronn microscopic digital twin.

Responsibilities:
    - Phase 1 (Calibration): ingest data, calibrate demand, validate physics.
    - Phase 2 (Sandbox): run experiments (disaster closure / adaptive control).

The simulation loop references stochastic behavior (e.g., Nagel-Schreckenberg)
via SUMO driver imperfection parameters to capture human variability.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from python_sim.analytics import (
    EconomicImpactCalculator,
    EmissionsAnalyzer,
    FundamentalDiagramValidator,
    StudentStressAnalyzer,
    TransitDelayTracker,
)
from python_sim.config import SimulationSettings
from python_sim.data_pipeline import DemandCalibrator, MobiDataLoader, OSMNetworkBuilder
from python_sim.simulation import AdaptiveSignalController, ConstructionEventManager, SUMOInitializer
from python_sim.utils import get_logger

logger = get_logger("python_sim.main")


class SimulationController:
    """High-level controller coordinating calibration + experiments."""

    def __init__(self, settings: SimulationSettings):
        self.settings = settings
        self.sumo = SUMOInitializer(config_path=settings.sumo_config)
        self.construction_manager = ConstructionEventManager(target_edge=settings.scenario_edges[0])
        self.adaptive_controller = AdaptiveSignalController(controlled_tls=[], phase_map={})
        self.detector_validator = FundamentalDiagramValidator(output_dir=settings.output_dir / "validation")
        self.student_analyzer = StudentStressAnalyzer(student_vehicle_ids=[])
        self.economic_calc = EconomicImpactCalculator(hourly_value_eur=25.0)
        self.emission_analyzer = EmissionsAnalyzer(emission_file=settings.output_dir / "emissions.csv")
        self.transit_tracker = TransitDelayTracker()

    # ------------------------------------------------------------------ Phase 1
    def run_calibration(self) -> None:
        """Calibrate the model so simulated volumes match real-world counts."""
        logger.info("Starting calibration phase")
        mobi_loader = MobiDataLoader(
            base_url="https://api.mobidata-bw.de",
            api_key=None,
            cache_dir=self.settings.project_root / "cache/mobidata",
        )
        osm_builder = OSMNetworkBuilder(
            place_name="Heilbronn, Weipertstraße",
            cache_dir=self.settings.project_root / "cache/osm",
        )

        logger.info("Fetching detector counts and building OSM network")
        # Placeholder: fetch counts + network, then convert to SUMO.
        # counts = mobi_loader.fetch_detector_counts(...)
        graph = osm_builder.download_network()
        osm_builder.export_to_sumo(graph, self.settings.project_root / "python_sim/build")

        calibrator = DemandCalibrator(target_counts=None)  # type: ignore[arg-type]
        # Placeholder for running iterative reweighting using calibrator.
        logger.info("Calibration placeholder finished")

    # ------------------------------------------------------------------ Phase 2
    def run_sandbox(self, duration_steps: int = 3600, gui: bool = False) -> None:
        """Run sandbox experiments (construction lanes + adaptive signals)."""
        logger.info("Launching SUMO sandbox")
        process = self.sumo.launch(gui=gui)
        try:
            for step in range(duration_steps):
                # TODO: connect to TraCI and fetch state; placeholder prints.
                if step == 600:
                    self.construction_manager.apply_closure(step)
                if step == 2400:
                    self.construction_manager.revert_closure(step)
                self.adaptive_controller.update(step)
        finally:
            process.terminate()
            logger.info("SUMO shutdown complete")

    # ------------------------------------------------------------------ Analytics
    def post_process(self) -> None:
        """Run analytics modules once simulation outputs are available."""
        logger.info("Running analytics post-processing")
        # Example placeholders:
        # fd_path = self.detector_validator.plot(detector_df, detector_id="D1")
        # stress_scores = self.student_analyzer.compute_stress_scores(arrivals_df)
        # emissions = self.emission_analyzer.aggregate()
        # transit_stats = self.transit_tracker.summarize(transit_df)
        # econ_loss = self.economic_calc.compute_loss(hours_lost=42.0)
        logger.info("Analytics placeholder complete")


def load_settings(project_root: Optional[Path] = None) -> SimulationSettings:
    """Convenience helper to instantiate default settings."""
    root = project_root or Path(__file__).resolve().parent.parent
    return SimulationSettings(
        project_root=root,
        sumo_config=root / "python_sim/configs/base.sumocfg",
        calibration_detectors=["D1", "D2"],
        scenario_edges=["edge_weipertstrasse"],
    )


if __name__ == "__main__":
    controller = SimulationController(load_settings())
    controller.run_calibration()
    controller.run_sandbox(gui=False)
    controller.post_process()

