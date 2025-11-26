# Heilbronn Hybrid Traffic Simulation — Full Python Implementation (Starter)
# Repository layout (single-file representation for the canvas)

# FILE: README.md
"""
Heilbronn Hybrid Traffic Simulation — Full Python Implementation

This repository contains a Python-first hybrid pipeline that orchestrates:
- MATSim (Java) as the mesoscopic engine (invoked and controlled from Python)
- SUMO (microscopic) controlled by TraCI (Python)
- A HybridServer (Python) that synchronizes MATSim outputs and SUMO micro-corrections
- A REST API (FastAPI) for scenario uploads, run control, and querying results

Important: MATSim remains a Java library; this pipeline controls MATSim as a subprocess and parses its outputs.

Quick start (developer machine):
- Install Java (11+), SUMO, Python 3.11
- Create virtualenv and install requirements: `pip install -r requirements.txt`
- Place your data under `data/` (OSM, GTFS, detectors, od_matrix)
- Build MATSim jar (or use provided matsim-core jar) and place under `third_party/matsim/`
- Start API server: `uvicorn api.server:app --reload --port 8000`
- Use API endpoints to upload data and run scenarios.
"""
 #test
# FILE: requirements.txt
"""
fastapi
uvicorn[standard]
httpx
pydantic
traci==1.16.0
sumolib
numpy
pandas
geopandas
pyyaml
aiofiles
python-multipart
py-cma
requests
"""

# FILE: docker/Dockerfile.python
"""
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
"""

# FILE: orchestrator/run_hybrid.py
"""
Entrypoint to run full hybrid pipeline: MATSim -> hotspot detection -> SUMO micro runs -> reintegration
"""
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

"""

# FILE: matsim/matsim_runner.py
"""
Wrapper that invokes MATSim as a subprocess, monitors progress, and parses events/outputs.
"""
from pathlib import Path
import subprocess
import shlex
import xml.etree.ElementTree as ET
import json
import logging

class MATSimRunner:
    def __init__(self, data_dir: Path, output_dir: Path, matsim_jar: str = 'third_party/matsim/matsim.jar'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.matsim_jar = Path(matsim_jar)

    def run_baseline(self, scenario: dict = None):
        # Build MATSim config dynamically or use templates
        config = self._build_config(scenario)
        cfg_path = self.output_dir / 'matsim_config.xml'
        with open(cfg_path, 'w') as f:
            f.write(config)
        cmd = f'java -Xms2g -Xmx6g -jar "{self.matsim_jar}" {cfg_path}'
        logging.info(f'Launching MATSim: {cmd}')
        proc = subprocess.run(shlex.split(cmd), capture_output=True, text=True)
        if proc.returncode != 0:
            logging.error(proc.stderr)
            raise RuntimeError('MATSim failed')
        # parse outputs
        events = self._parse_events(self.output_dir / 'events.xml')
        link_stats = self._parse_linkstats(self.output_dir / 'linkstats.csv')
        return {'events': events, 'link_stats': link_stats}

    def _build_config(self, scenario: dict = None) -> str:
        # minimal matSim config template. In practice replace with full config.
        return '<config/>\n'

    def _parse_events(self, events_file: Path):
        if not events_file.exists():
            return []
        # For performance, don't parse huge files fully; return summary aggregated per link
        # placeholder: return empty
        return []

    def _parse_linkstats(self, linkstats_file: Path):
        if not linkstats_file.exists():
            return []
        import csv
        rows = []
        with open(linkstats_file) as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append(r)
        return rows

    def detect_hotspots(self, matsim_res: dict, top_n: int = 10):
        # simple detection: sort links by totalDelay (if available)
        stats = matsim_res.get('link_stats', [])
        if not stats:
            return []
        def delay_key(r):
            try:
                return float(r.get('delay', 0))
            except:
                return 0
        sorted_links = sorted(stats, key=delay_key, reverse=True)
        return [r['linkId'] for r in sorted_links[:top_n]]

    def run_with_corrections(self, corrections):
        # write corrections into MATSim input (link travel times) and rerun
        return self.run_baseline(scenario={'corrections': corrections})

"""

# FILE: sumo/sumo_runner.py
"""
SUMO microsim control via TraCI for hotspot subnetworks.
"""
from pathlib import Path
import traci
import subprocess
import logging
import random
import xml.etree.ElementTree as ET

class SUMORunner:
    def __init__(self, data_dir: Path, output_dir: Path, sumo_binary: str = 'sumo'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.sumo_binary = sumo_binary

    def run_hotspots(self, hotspots: list):
        results = {}
        for link_id in hotspots:
            try:
                res = self._run_hotspot(link_id)
                results[link_id] = res
            except Exception as e:
                logging.exception(f'Hotspot {link_id} failed: {e}')
        return results

    def _run_hotspot(self, link_id: str):
        # Extract OSM subset and convert to SUMO net (placeholder)
        bbox = self._link_bbox(link_id)
        netfile = self.output_dir / f'sumo_hotspot_{link_id}.net.xml'
        routefile = self.output_dir / f'sumo_hotspot_{link_id}.rou.xml'
        # run sumo headless with TraCI
        cmd = [self.sumo_binary, '-n', str(netfile), '-r', str(routefile), '--seed', str(random.randint(0,10000)), '--duration-log.statistics']
        logging.info('Running SUMO: ' + ' '.join(cmd))
        proc = subprocess.run(cmd, capture_output=True, text=True)
        # parse outputs - placeholder
        return {'avg_delay': random.random()*30}

    def _link_bbox(self, link_id: str):
        # map link id to bbox using data; placeholder
        return (0,0,0,0)

"""

# FILE: hybrid/hybrid_server.py
"""
Simple hybrid server that maps SUMO micro results to MATSim link corrections and vice versa.
"""
from typing import Dict
import logging

class HybridServer:
    def __init__(self, matsim_runner, sumo_runner):
        self.matsim = matsim_runner
        self.sumo = sumo_runner

    def reintegrate(self, matsim_res, micro_results: Dict):
        # For each MATSim link, if micro result is available, compute corrected travel time multiplier
        corrections = {}
        for link in matsim_res.get('link_stats', []):
            lid = link.get('linkId')
            if lid in micro_results:
                micro = micro_results[lid]
                # simplistic: corrected_tt = original_tt + micro.avg_delay
                try:
                    orig_tt = float(link.get('time', 0))
                except:
                    orig_tt = 0
                corrected = orig_tt + float(micro.get('avg_delay', 0))
                corrections[lid] = {'orig': orig_tt, 'corrected': corrected}
        return corrections

"""

# FILE: api/server.py
"""
FastAPI server to control the pipeline and query results
"""
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import uvicorn
from orchestrator.run_hybrid import HybridOrchestrator

app = FastAPI(title='Heilbronn Hybrid Traffic API')

DATA_DIR = Path('data')
OUTPUT_DIR = Path('output')
DATA_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

orchestrator = HybridOrchestrator(DATA_DIR, OUTPUT_DIR)

@app.post('/upload/osm')
async def upload_osm(file: UploadFile = File(...)):
    dest = DATA_DIR / 'heilbronn.osm'
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return {'status': 'ok', 'path': str(dest)}

@app.post('/upload/gtfs')
async def upload_gtfs(file: UploadFile = File(...)):
    dest = DATA_DIR / file.filename
    with open(dest, 'wb') as f:
        shutil.copyfileobj(file.file, f)
    return {'status': 'ok', 'path': str(dest)}

@app.post('/run')
async def run_pipeline(background_tasks: BackgroundTasks):
    background_tasks.add_task(orchestrator.run_full_pipeline)
    return {'status': 'started'}

@app.get('/results')
def get_results():
    res_file = OUTPUT_DIR / 'final_results.json'
    if not res_file.exists():
        return JSONResponse({'status': 'not ready'}, status_code=202)
    import json
    return json.loads(res_file.read_text())

if __name__ == '__main__':
    uvicorn.run('api.server:app', host='0.0.0.0', port=8000, reload=True)
"""

# FILE: api/routes/trafficlights.py (example route module)
"""
# placeholder for more refined traffic-light control endpoints
"""

# FILE: utils/file_helpers.py
"""
Small helper utilities used across modules.
"""
from pathlib import Path
import json


def save_json(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(obj, f, indent=2)

def load_json(path: Path):
    with open(path) as f:
        return json.load(f)

"""

# FILE: config/pipeline.yaml
"""
matsim:
  jar: third_party/matsim/matsim.jar
  iterations: 100
sumo:
  binary: sumo
  seeds: 5
pipeline:
  hotspot_top_n: 10
"""

# End of single-file repository representation
# (actual repo will contain files under their respective directories)
