"""
Build and preprocess the OpenStreetMap network covering Heilbronn (Weipertstraße).

This builder focuses on:
    - Pulling the bounding box using OSMnx.
    - Cleaning lane / speed attributes for SUMO network generation.
    - Injecting detector locations and public transport stops for analytics.
"""
from __future__ import annotations

import os
import copy
import shutil
import subprocess
import textwrap
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

import networkx as nx
import osmnx as ox
import requests


@dataclass
class OSMNetworkBuilder:
    """Handles downloading and exporting SUMO-ready networks."""

    place_name: str
    cache_dir: Path
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    sumo_home: Path | None = None
    _last_bbox: Tuple[float, float, float, float] | None = field(default=None, init=False)

    def download_network(self, bbox: Tuple[float, float, float, float] | None = None) -> nx.MultiDiGraph:
        """Download the road network for the study area."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # if bbox:
        #     north, south, east, west = bbox
        #     graph = ox.graph_from_bbox(
        #         bbox, network_type="drive_service"
        #     )
        #     self._last_bbox = (
        #         min(north, south),
        #         max(north, south),
        #         min(west, east),
        #         max(west, east),
        #     )
        # else:
        #     graph = ox.graph_from_place(self.place_name, network_type="drive_service")
        #     self._last_bbox = self._graph_bbox(graph)
        # return ox.add_edge_speeds(ox.add_edge_lengths(graph))

        graph = ox.graph_from_xml("python_sim/data/heilbronn-weipertstrasse.osm")
        return ox.add_edge_speeds(ox.distance.add_edge_lengths(graph))

    def export_to_sumo(self, graph: nx.MultiDiGraph, output_dir: Path) -> Path:
        """Convert the OSM graph into a SUMO .net.xml via netconvert."""
        output_dir.mkdir(parents=True, exist_ok=True)
        graphml_path = output_dir / "heilbronn_weipert.graphml"
        ox.save_graphml(graph, filepath=graphml_path)

        bbox = self._last_bbox or self._graph_bbox(graph)
        
        # 1. FIX: Define the osm_extract path (The missing line)
        osm_extract = self.cache_dir / "heilbronn_weipert.osm.xml"
        
        # 2. Re-download the raw OSM data (Crucial to address 'No nodes loaded' if corrupted)
        self._download_osm_extract(bbox, osm_extract)

        # 3. Setup Environment for netconvert (FIX: SUMO_HOME issue)
        sumo_bin_path = str(self.sumo_home / "bin" / "netconvert")
        env = copy.copy(os.environ)
        if self.sumo_home:
            env["SUMO_HOME"] = str(self.sumo_home)

        # 4. Define the command
        net_path = output_dir / "heilbronn_weipert.net.xml"
        cmd = [
            self._resolve_netconvert(),
            "--osm-files",
            str(osm_extract),
            "--output-file",
            str(net_path),
            "--geometry.remove",
            "--roundabouts.guess",
            "--junctions.corner-detail",
            "5",
            "--ramps.guess",
            "--tls.join",
        ]
        
        # 5. Execute command
        subprocess.run(cmd, check=True, env=env)
        
        return net_path

    # ------------------------------------------------------------------ helpers
    def _download_osm_extract(
        self, bbox: Tuple[float, float, float, float], target_path: Path
    ) -> Path:
        """Pull raw OSM data for the bbox so that netconvert can ingest it."""
        # Note: We use the format expected by the Overpass API: south,west,north,east
        south, north, west, east = bbox
        
        # This is the standard, robust query that netconvert expects
        query = textwrap.dedent(
            f"""
            [out:xml][timeout:60];
            (
              node({south},{west},{north},{east});
              way({south},{west},{north},{east});
              relation({south},{west},{north},{east});
            );
            (._;>;);
            out;
            """
        ).strip()
        response = requests.post(self.overpass_url, data={"data": query}, timeout=120)
        response.raise_for_status()
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(response.content)
        return target_path

    def _graph_bbox(self, graph: nx.MultiDiGraph) -> Tuple[float, float, float, float]:
        """Compute bounding box from graph nodes."""
        lats = [data["y"] for _, data in graph.nodes(data=True)]
        lons = [data["x"] for _, data in graph.nodes(data=True)]
        return (min(lats), max(lats), min(lons), max(lons))

    def _resolve_netconvert(self) -> str:
        """Locate the netconvert binary from SUMO_HOME or PATH."""
        candidate = shutil.which("netconvert")
        if candidate:
            return candidate
        env_home = os.environ.get("SUMO_HOME")
        if env_home:
            candidate_path = Path(env_home) / "bin" / "netconvert"
            if candidate_path.exists():
                return str(candidate_path)
        if self.sumo_home:
            candidate_path = Path(self.sumo_home) / "bin" / "netconvert"
            if candidate_path.exists():
                return str(candidate_path)
        raise FileNotFoundError(
            "netconvert binary not found. Ensure SUMO is installed and SUMO_HOME/bin is on PATH."
        )

