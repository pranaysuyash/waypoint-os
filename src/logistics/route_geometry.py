"""
src/logistics/route_geometry.py — Geodesic Path Optimization & Route Geometry Intelligence (Area #17).

Implements:
1. Geodesic / Great-Circle distance and initial bearing calculations via Haversine.
2. GeodesicPathOptimizer: Waypoint sequencing via exact permutation and 2-opt heuristic optimization.
3. detect_backtracking: Detects inefficient zig-zagging itineraries, excess distance, and suggests optimal convex/sequential ordering.
4. detect_open_jaw_surface_segments: Identifies open-jaw / ARNK flight gaps and automatically inserts surface segments (`//`).
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


# Earth Radius Constants
EARTH_RADIUS_KM = 6371.0088
EARTH_RADIUS_NM = 3440.065
EARTH_RADIUS_MILES = 3958.756

# Canonical Coordinates Reference Database for Major Global Hubs & Cities
AIRPORT_COORDINATES_DB: Dict[str, Tuple[float, float]] = {
    # North America
    "JFK": (40.6413, -73.7781),
    "EWR": (40.6895, -74.1745),
    "LGA": (40.7769, -73.8740),
    "BOS": (42.3656, -71.0096),
    "IAD": (38.9531, -77.4565),
    "DCA": (38.8512, -77.0402),
    "ORD": (41.9742, -87.9073),
    "MIA": (25.7959, -80.2870),
    "FLL": (26.0742, -80.1506),
    "LAX": (33.9416, -118.4085),
    "SFO": (37.6213, -122.3790),
    "SEA": (47.4502, -122.3088),
    "DEN": (39.8561, -104.6737),
    "KASE": (39.2232, -106.8688),
    "ASE": (39.2232, -106.8688),
    # Europe
    "LHR": (51.4700, -0.4543),
    "LGW": (51.1537, -0.1821),
    "CDG": (49.0097, 2.5479),
    "ORY": (48.7262, 2.3652),
    "FRA": (50.0379, 8.5622),
    "MUC": (48.3537, 11.7750),
    "AMS": (52.3105, 4.7683),
    "FCO": (41.8003, 12.2389),
    "FLR": (43.8100, 11.2051),
    "VCE": (45.5053, 12.3519),
    "MXP": (45.6301, 8.7255),
    "BCN": (41.2974, 2.0833),
    "MAD": (40.4839, -3.5680),
    "ZRH": (47.4582, 8.5555),
    "GVA": (46.2370, 6.1092),
    "LSZS": (46.5342, 9.8841),
    "VIE": (48.1103, 16.5697),
    "CPH": (55.6180, 12.6508),
    "HEL": (60.3172, 24.9633),
    "ARN": (59.6519, 17.9186),
    "OSL": (60.1976, 11.1004),
    "DUB": (53.4264, -6.2499),
    "EDI": (55.9500, -3.3725),
    "ATH": (37.9364, 23.9484),
    "LIS": (38.7742, -9.1342),
    "PRG": (50.1008, 14.2600),
    "WAW": (52.1657, 20.9671),
    "BUD": (47.4369, 19.2556),
    # Asia & Middle East
    "DXB": (25.2532, 55.3657),
    "AUH": (24.4330, 54.6511),
    "DOH": (25.2731, 51.6081),
    "SIN": (1.3644, 103.9915),
    "BKK": (13.6900, 100.7501),
    "HND": (35.5494, 139.7798),
    "NRT": (35.7720, 140.3929),
    "KIX": (34.4347, 135.2441),
    "FUK": (33.5859, 130.4507),
    "ICN": (37.4602, 126.4407),
    "HKG": (22.3080, 113.9185),
    "DEL": (28.5562, 77.1000),
    "BOM": (19.0896, 72.8656),
    "BLR": (13.1986, 77.7066),
    # Oceania
    "SYD": (-33.9399, 151.1753),
    "MEL": (-37.6690, 144.8410),
    "AKL": (-37.0082, 174.7850),
}


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    unit: str = "km",
) -> float:
    """
    Computes Great-Circle distance between two coordinates using the Haversine formula.

    Args:
        lat1: Latitude of point 1 in decimal degrees.
        lon1: Longitude of point 1 in decimal degrees.
        lat2: Latitude of point 2 in decimal degrees.
        lon2: Longitude of point 2 in decimal degrees.
        unit: 'km', 'nm' (nautical miles), or 'mi' (statute miles).

    Returns:
        Great-Circle distance in the requested unit.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    # Numerical stability clamp for identical / antipodal coords
    a = max(0.0, min(1.0, a))
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    unit_clean = unit.strip().lower()
    if unit_clean in ("nm", "nautical", "nautical_miles"):
        r = EARTH_RADIUS_NM
    elif unit_clean in ("mi", "miles", "statute_miles"):
        r = EARTH_RADIUS_MILES
    else:
        r = EARTH_RADIUS_KM

    return r * c


def calculate_initial_bearing(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculates initial compass bearing (forward azimuth) from point 1 to point 2 in degrees (0..360).
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_lambda = math.radians(lon2 - lon1)

    y = math.sin(delta_lambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing_deg = math.degrees(math.atan2(y, x))
    return (bearing_deg + 360.0) % 360.0


def _extract_coordinates(stop: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    """Extracts (latitude, longitude) from various dictionary schemas or airport codes."""
    # 1. Direct lat/lng keys
    lat = stop.get("lat") or stop.get("latitude")
    lon = stop.get("lng") or stop.get("lon") or stop.get("longitude")

    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (ValueError, TypeError):
            pass

    # 2. Coordinates embedded in 'coordinates' or 'location' dict/tuple
    coords = stop.get("coordinates") or stop.get("location")
    if isinstance(coords, (list, tuple)) and len(coords) >= 2:
        try:
            return float(coords[0]), float(coords[1])
        except (ValueError, TypeError):
            pass
    elif isinstance(coords, dict):
        c_lat = coords.get("lat") or coords.get("latitude")
        c_lon = coords.get("lng") or coords.get("lon") or coords.get("longitude")
        if c_lat is not None and c_lon is not None:
            try:
                return float(c_lat), float(c_lon)
            except (ValueError, TypeError):
                pass

    # 3. Airport code lookup
    for key in ("airport", "airport_code", "iata", "code", "id", "city"):
        val = stop.get(key)
        if isinstance(val, str):
            code_upper = val.strip().upper()
            if code_upper in AIRPORT_COORDINATES_DB:
                return AIRPORT_COORDINATES_DB[code_upper]

    return None


def _get_stop_identifier(stop: Dict[str, Any], index: int) -> str:
    """Returns the most human-readable identifier for a stop."""
    for key in ("id", "code", "airport", "name", "city", "iata"):
        val = stop.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return f"Stop_{index + 1}"


@dataclass(slots=True)
class GeodesicPathOptimizer:
    """
    Optimizes geodesic paths and calculates route distances for multi-destination itineraries.
    """

    @classmethod
    def calculate_total_distance(
        cls,
        stops: Sequence[Dict[str, Any]],
        unit: str = "km",
    ) -> float:
        """
        Computes the sequential great-circle path distance across a list of waypoint stops.
        """
        if len(stops) < 2:
            return 0.0

        coords: List[Tuple[float, float]] = []
        for stop in stops:
            c = _extract_coordinates(stop)
            if c is not None:
                coords.append(c)

        if len(coords) < 2:
            return 0.0

        total_d = 0.0
        for i in range(len(coords) - 1):
            total_d += haversine_distance(
                coords[i][0], coords[i][1],
                coords[i + 1][0], coords[i + 1][1],
                unit=unit,
            )
        return total_d

    @classmethod
    def optimize_waypoint_order(
        cls,
        stops: List[Dict[str, Any]],
        fix_start: bool = True,
        fix_end: bool = False,
        unit: str = "km",
    ) -> List[Dict[str, Any]]:
        """
        Finds the optimal sequencing of waypoints to minimize total geodesic path distance.

        - If fix_start is True, the first stop remains at index 0.
        - If fix_end is True, the last stop remains at the final index.
        - For N <= 8 waypoints, exact global search is computed.
        - For N > 8 waypoints, Nearest-Neighbor with 2-Opt local search refinement is used.
        """
        n = len(stops)
        if n <= 2:
            return list(stops)

        # Extract coordinates
        coords: List[Optional[Tuple[float, float]]] = [_extract_coordinates(s) for s in stops]

        # If any stop has missing coordinates, return unmodified list
        if any(c is None for c in coords):
            return list(stops)

        valid_coords: List[Tuple[float, float]] = [c for c in coords if c is not None]

        # Distance matrix
        dist_matrix: List[List[float]] = [
            [
                haversine_distance(
                    valid_coords[i][0], valid_coords[i][1],
                    valid_coords[j][0], valid_coords[j][1],
                    unit=unit,
                )
                for j in range(n)
            ]
            for i in range(n)
        ]

        def tour_distance(order: Sequence[int]) -> float:
            return sum(dist_matrix[order[i]][order[i + 1]] for i in range(len(order) - 1))

        # 1. Exact Permutation Search for small N (<= 8)
        if n <= 8:
            if fix_start and fix_end:
                middle_indices = list(range(1, n - 1))
                best_order = [0] + middle_indices + [n - 1]
                best_dist = tour_distance(best_order)
                for perm in itertools.permutations(middle_indices):
                    cand = [0] + list(perm) + [n - 1]
                    d = tour_distance(cand)
                    if d < best_dist:
                        best_dist = d
                        best_order = list(cand)
                return [stops[i] for i in best_order]
            elif fix_start:
                sub_indices = list(range(1, n))
                best_order = [0] + sub_indices
                best_dist = tour_distance(best_order)
                for perm in itertools.permutations(sub_indices):
                    cand = [0] + list(perm)
                    d = tour_distance(cand)
                    if d < best_dist:
                        best_dist = d
                        best_order = list(cand)
                return [stops[i] for i in best_order]
            else:
                all_indices = list(range(n))
                best_order = all_indices
                best_dist = tour_distance(best_order)
                for perm in itertools.permutations(all_indices):
                    cand = list(perm)
                    d = tour_distance(cand)
                    if d < best_dist:
                        best_dist = d
                        best_order = list(cand)
                return [stops[i] for i in best_order]

        # 2. Nearest Neighbor + 2-Opt Heuristic for N > 8
        # Step A: Nearest Neighbor Tour Construction
        unvisited = set(range(n))
        start_idx = 0 if fix_start else 0
        unvisited.remove(start_idx)
        current_tour = [start_idx]

        target_end = (n - 1) if fix_end else None
        if target_end is not None and target_end in unvisited:
            unvisited.remove(target_end)

        curr = start_idx
        while unvisited:
            next_node = min(unvisited, key=lambda idx: dist_matrix[curr][idx])
            current_tour.append(next_node)
            unvisited.remove(next_node)
            curr = next_node

        if target_end is not None:
            current_tour.append(target_end)

        # Step B: 2-Opt Refinement
        improved = True
        start_opt = 1 if fix_start else 0
        end_opt = (n - 1) if fix_end else n

        max_iterations = 200
        iteration = 0
        while improved and iteration < max_iterations:
            improved = False
            iteration += 1
            for i in range(start_opt, end_opt - 1):
                for j in range(i + 1, end_opt):
                    # Evaluate 2-opt swap
                    new_tour = current_tour[:i] + current_tour[i:j + 1][::-1] + current_tour[j + 1:]
                    if tour_distance(new_tour) + 1e-6 < tour_distance(current_tour):
                        current_tour = new_tour
                        improved = True
                        break
                if improved:
                    break

        return [stops[i] for i in current_tour]


def detect_backtracking(
    stops: List[Dict[str, Any]],
) -> Tuple[bool, float, List[str]]:
    """
    Analyzes an itinerary stop sequence to detect suboptimal zigzagging/backtracking.

    Args:
        stops: List of stop dictionaries with coordinates or airport codes.

    Returns:
        tuple of (has_backtracking: bool, excess_distance_km: float, suggested_order_ids: List[str])
    """
    if len(stops) < 3:
        ids = [_get_stop_identifier(s, i) for i, s in enumerate(stops)]
        return False, 0.0, ids

    # Calculate current sequential distance
    current_dist = GeodesicPathOptimizer.calculate_total_distance(stops, unit="km")

    # Find optimal sequence preserving the trip starting origin
    optimized_stops = GeodesicPathOptimizer.optimize_waypoint_order(stops, fix_start=True, unit="km")
    optimal_dist = GeodesicPathOptimizer.calculate_total_distance(optimized_stops, unit="km")

    suggested_ids = [_get_stop_identifier(s, i) for i, s in enumerate(optimized_stops)]

    if optimal_dist <= 0.0:
        return False, 0.0, suggested_ids

    excess_distance = max(0.0, current_dist - optimal_dist)
    excess_ratio = excess_distance / optimal_dist

    # Detect bearing reversals (ping-ponging between destinations)
    coords: List[Optional[Tuple[float, float]]] = [_extract_coordinates(s) for s in stops]
    valid_coords = [c for c in coords if c is not None]

    bearing_reversals = 0
    if len(valid_coords) >= 3:
        for i in range(len(valid_coords) - 2):
            b1 = calculate_initial_bearing(
                valid_coords[i][0], valid_coords[i][1],
                valid_coords[i + 1][0], valid_coords[i + 1][1],
            )
            b2 = calculate_initial_bearing(
                valid_coords[i + 1][0], valid_coords[i + 1][1],
                valid_coords[i + 2][0], valid_coords[i + 2][1],
            )
            angle_diff = abs(b1 - b2)
            if angle_diff > 180.0:
                angle_diff = 360.0 - angle_diff
            if angle_diff >= 135.0:
                bearing_reversals += 1

    # Backtracking is flagged if excess distance > 5% and noticeable distance (>30km), or bearing reversal
    has_backtracking = (excess_distance > 30.0 and excess_ratio >= 0.05) or (bearing_reversals >= 1 and excess_distance > 20.0)

    return has_backtracking, round(excess_distance, 2), suggested_ids


def detect_open_jaw_surface_segments(
    legs: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Inspects multi-leg flight sequences to detect open-jaw ground transfers (ARNK / Surface //).
    Automatically inserts explicit surface segment items where arrival != subsequent departure.

    Args:
        legs: Ordered list of flight leg dictionaries.

    Returns:
        Enriched list of itinerary segments including flight legs and clearly marked surface segments (`//`).
    """
    if not legs:
        return []

    result_segments: List[Dict[str, Any]] = []

    def get_origin(leg: Dict[str, Any]) -> str:
        for k in ("origin", "from_airport", "origin_iata", "departure_airport", "from", "origin_code"):
            v = leg.get(k)
            if v:
                return str(v).strip().upper()
        return ""

    def get_destination(leg: Dict[str, Any]) -> str:
        for k in ("destination", "to_airport", "dest_iata", "arrival_airport", "to", "destination_code"):
            v = leg.get(k)
            if v:
                return str(v).strip().upper()
        return ""

    for i in range(len(legs)):
        current_leg = dict(legs[i])
        result_segments.append(current_leg)

        if i < len(legs) - 1:
            current_dest = get_destination(current_leg)
            next_orig = get_origin(legs[i + 1])

            # If current arrival doesn't match next departure, insert surface segment (Open-Jaw / ARNK //)
            if current_dest and next_orig and current_dest != next_orig:
                # Calculate surface distance if coordinates available
                coord_from = AIRPORT_COORDINATES_DB.get(current_dest)
                coord_to = AIRPORT_COORDINATES_DB.get(next_orig)
                surface_dist_km: Optional[float] = None
                if coord_from and coord_to:
                    surface_dist_km = round(
                        haversine_distance(coord_from[0], coord_from[1], coord_to[0], coord_to[1], unit="km"),
                        1,
                    )

                surface_segment = {
                    "segment_type": "SURFACE",
                    "surface_indicator": "//",
                    "is_open_jaw_surface": True,
                    "origin": current_dest,
                    "destination": next_orig,
                    "estimated_surface_distance_km": surface_dist_km,
                    "description": (
                        f"Overland surface sector required: Traveler arrives at {current_dest} "
                        f"and departs next leg from {next_orig} (Open-Jaw //)."
                    ),
                }
                result_segments.append(surface_segment)

    return result_segments
