from pathlib import Path
import subprocess
import json
import tempfile
import logging
from hybrid.hybrid_server import HybridServer
from matsim.matsim_runner import MATSimRunner
from sumo.sumo_runner import SUMORunner

logging.basicConfig(level=logging.INFO)

class HybridOrchestrator:
    def __init__(self, data_dir: str = 'data', output_dir: str = 'output'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.matsim = MATSimRunner(self.data_dir, self.output_dir)
        self.sumo = SUMORunner(self.data_dir, self.output_dir)
        self.hybrid_server = HybridServer(self.matsim, self.sumo)

    def run_full_pipeline(self, scenario: dict = None):
        logging.info('Running MATSim baseline...')
        matsim_res = self.matsim.run_baseline(scenario)
        logging.info('Detecting hotspots...')
        hotspots = self.matsim.detect_hotspots(matsim_res, top_n=10)
        logging.info(f'Hotspots found: {hotspots}')
        logging.info('Running SUMO micro-simulations for hotspots...')
        micro_results = self.sumo.run_hotspots(hotspots)
        logging.info('Reintegrating micro results into MATSim...')
        reintegrated = self.hybrid_server.reintegrate(matsim_res, micro_results)
        logging.info('Running MATSim corrected scenario...')
        final_res = self.matsim.run_with_corrections(reintegrated)
        logging.info('Pipeline complete. Writing outputs...')
        with open(self.output_dir / 'final_results.json', 'w') as f:
            json.dump(final_res, f, indent=2)
        return final_res

if __name__ == '__main__':
    orc = HybridOrchestrator()
    res = orc.run_full_pipeline()
    print('Done. Results in output/final_results.json')