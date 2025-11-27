"""Geospatial helper functions."""
from __future__ import annotations

import math
from typing import Tuple


def haversine_distance_km(coord_a: Tuple[float, float], coord_b: Tuple[float, float]) -> float:
    """Great-circle distance between two lat/lon pairs."""
    lat1, lon1 = map(math.radians, coord_a)
    lat2, lon2 = map(math.radians, coord_b)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371.0 * c

