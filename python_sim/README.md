# python_sim Architecture

```
python_sim/
├── analytics/              # Validation + impact metrics
├── config/                 # Dataclass-based settings
├── data_pipeline/          # Real-world data ingestion & calibration helpers
├── simulation/             # TraCI loops, events, adaptive control
├── utils/                  # Shared helpers (logging, geo math)
├── main_controller.py      # Phase 1 (calibration) + Phase 2 (sandbox) orchestrator
└── requirements.txt        # Narrow virtual-env dependencies
```

## Phase 1 – Calibration
- `data_pipeline/mobi_data_loader.py`: pull detector counts + GTFS from MobiData BW.
- `data_pipeline/osm_network_builder.py`: download OSM, export SUMO network.
- `data_pipeline/demand_calibrator.py`: close the loop between observed counts and simulated flows.
- `analytics/validation.py`: produce Fundamental Diagrams that demonstrate microscopic realism.

## Phase 2 – What-If Sandbox
- `simulation/sumo_initializer.py`: launch SUMO/TraCI with deterministic seeds.
- `simulation/scenario_events.py`: lane closures that emulate Weipertstraße works.
- `simulation/adaptive_signal_controller.py`: scaffold for Markov / RL signal logic.
- `analytics/student_metrics.py`, `economic_metrics.py`, `sustainability_metrics.py`, `transit_metrics.py`:
  quantify impacts on students, economics, CO2, and public transport delays.

`main_controller.py` stitches both phases together and exposes placeholders to inject the construction event and adaptive logic. The coordinator references stochastic driver behavior (e.g., Nagel–Schreckenberg) via SUMO driver imperfection parameters to capture human error.

## Phase 1 quick start

1. Install dependencies (inside the `tom` conda env):
   ```bash
   pip install -r python_sim/requirements.txt
   ```
2. Ensure SUMO is discoverable:
   ```bash
   export SUMO_HOME=/Library/Frameworks/EclipseSUMO.framework/Versions/1.25.0/EclipseSUMO
   export PATH="$SUMO_HOME/bin:$PATH"
   ```
3. Download the Weipertstraße network and convert it to SUMO:
   ```bash
   python -m python_sim.cli.prepare_phase1 download-osm \
     --bbox "49.1500,49.1350,9.2250,9.1950"
   ```
   Adjust the bounding box as needed; the command drops `heilbronn_weipert.net.xml` under `python_sim/build/`.
4. Pull detector counts from MobiData BW (requires an API token stored as `MOBIDATA_API_TOKEN` in your shell or `.env`):
   ```bash
   python -m python_sim.cli.prepare_phase1 fetch-counts \
     --detector DETECTOR_ID_1 --detector DETECTOR_ID_2 \
     --start "2025-01-13T06:30:00" \
     --end   "2025-01-13T09:30:00"
   ```
   The command stores raw JSON/Parquet outputs in `python_sim/data/raw/mobidata/` for calibration routines.

Once the inputs are prepared, run `python python_sim/main_controller.py` to execute the calibration scaffolding, then extend the controller with your specific detector mappings and demand tuning logic.

