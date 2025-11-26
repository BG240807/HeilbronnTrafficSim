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