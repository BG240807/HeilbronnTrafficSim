"""
Utilities for ingesting administrative traffic data (e.g., MobiData BW feeds).

This module is responsible for:
    - Authenticating against public administration APIs.
    - Downloading detector counts / GTFS feeds for calibration periods.
    - Normalizing the data into tidy pandas DataFrames for downstream use.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import requests


@dataclass
class MobiDataLoader:
    """Pulls and caches administrative traffic data for calibration windows."""

    base_url: str
    api_key: Optional[str]
    cache_dir: Path

    def _request(self, endpoint: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}
        base = self.base_url.rstrip("/")
        if endpoint:
            url = f"{base}/{endpoint.lstrip('/')}"
        else:
            url = base
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def fetch_detector_counts(
        self,
        detector_id: str,
        start_ts: str,
        end_ts: str,
        endpoint: str | None = None,
    ) -> pd.DataFrame:
        """Download detector counts for calibration; timestamps are ISO8601 strings."""
        resource = (endpoint or "traffic/counts").format(detector_id=detector_id)
        payload = self._request(
            resource,
            params={"detector_id": detector_id, "start": start_ts, "end": end_ts},
        )
        df = pd.DataFrame(payload["results"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)
        return df

    def fetch_transit_feed(self, feed_name: str) -> Path:
        """Download GTFS feeds to support public transport punctuality analysis."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        target = self.cache_dir / f"{feed_name}.zip"
        if target.exists():
            return target
        with requests.get(f"{self.base_url}/gtfs/{feed_name}", stream=True, timeout=60) as response:
            response.raise_for_status()
            target.write_bytes(response.content)
        return target

