"""
CLI helpers to bootstrap Phase 1 (data ingestion + network build) for
the Heilbronn Weipertstraße digital twin.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import typer
from dotenv import load_dotenv

from python_sim.data_pipeline import MobiDataLoader, OSMNetworkBuilder

app = typer.Typer(help="Utilities for preparing the Microscopic Digital Twin inputs.")


def _parse_bbox(bbox: str) -> Tuple[float, float, float, float]:
    """
    Parse a comma-separated bounding box string (north,south,east,west) into floats.
    """
    parts = [p.strip() for p in bbox.split(",")]
    if len(parts) != 4:
        raise typer.BadParameter("Expected four comma-separated values: north,south,east,west")
    n, s, e, w = map(float, parts)
    return (n, s, e, w)


@app.command("download-osm")
def download_osm(
    place: str = typer.Option("Heilbronn, Germany", help="Place name for OSMnx lookup."),
    bbox: Optional[str] = typer.Option(
        None,
        help="Optional bounding box override as 'north,south,east,west'. Defaults to the bounding box in config.",
    ),
    cache_dir: Path = typer.Option(
        Path("python_sim/cache/osm"), "--cache-dir", help="Where to cache downloaded OSM extracts."
    ),
    output_dir: Path = typer.Option(
        Path("python_sim/build"), "--output-dir", help="Directory for graphml + SUMO net"
    ),
    sumo_home: Optional[Path] = typer.Option(None, "--sumo-home", help="Override $SUMO_HOME"),
):
    """
    Download the Weipertstraße road network and convert it into a SUMO-ready net.xml.
    """
    load_dotenv()
    builder = OSMNetworkBuilder(
        place_name=place,
        cache_dir=cache_dir,
        sumo_home=sumo_home or (Path(os.environ["SUMO_HOME"]) if "SUMO_HOME" in os.environ else None),
    )
    bounds = _parse_bbox(bbox) if bbox else None
    graph = builder.download_network(bounds)
    net_path = builder.export_to_sumo(graph, output_dir)
    typer.echo(f"✅ Generated SUMO network at {net_path}")


@app.command("fetch-counts")
def fetch_counts(
    detectors: List[str] = typer.Option(..., "--detector", help="Detector IDs from MobiData BW"),
    start: str = typer.Option(..., help="Start timestamp (ISO 8601, e.g., 2025-01-15T06:30:00)"),
    end: str = typer.Option(..., help="End timestamp (ISO 8601, e.g., 2025-01-15T09:30:00)"),
    api_url: str = typer.Option(
        "https://verkehr.visum.de/api/mobidata-bw/traffic-count/v2",
        help="Base URL of the MobiData BW API endpoint.",
    ),
    endpoint: str = typer.Option(
        "traffic/counts",
        help="Endpoint appended to the base URL. Supports {detector_id} templating if needed.",
    ),
    cache_dir: Path = typer.Option(Path("python_sim/data/raw/mobidata"), "--cache-dir"),
    token_env: str = typer.Option(
        "MOBIDATA_API_TOKEN", help="Environment variable containing the API token"
    ),
):
    """
    Pull detector counts for a given time window and persist them as JSON.
    """
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)

    loader = MobiDataLoader(
        base_url=api_url,
        api_key=os.environ.get(token_env),
        cache_dir=cache_dir,
    )
    cache_dir.mkdir(parents=True, exist_ok=True)
    payload = {}
    for detector in detectors:
        typer.echo(f"Fetching counts for detector {detector}…")
        data = loader.fetch_detector_counts(
            detector_id=detector,
            start_ts=start_dt.isoformat(),
            end_ts=end_dt.isoformat(),
            endpoint=endpoint,
        )
        payload[detector] = json.loads(data.to_json(orient="records", date_format="iso"))
    out_path = cache_dir / f"counts_{start_dt.date()}_{end_dt.date()}.json"
    out_path.write_text(json.dumps(payload, indent=2))
    typer.echo(f"Saved aggregated counts to {out_path}")


if __name__ == "__main__":
    app()

