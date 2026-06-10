"""
Routing module:
  - Build weighted graph with NetworkX (Haversine edge weights + traffic factor)
  - Compute distances with Dijkstra (with memoised cache)
  - Solve small-scale TSP (≤ 15 nodes) via branch-and-bound + 2-opt + Or-opt
"""

from __future__ import annotations

import math
import random
from functools import lru_cache

import httpx
import networkx as nx

from backend.models.schemas import Order

# ---------------------------------------------------------------------------
# Haversine helper
# ---------------------------------------------------------------------------

def _haversine(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Compute the Haversine distance (km) between two lat/lng points."""
    R = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlng / 2) ** 2
    )
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------

def _validate_order_coordinates(orders: list[Order]) -> None:
    """Validate that all order coordinates are sane."""
    for o in orders:
        if math.isnan(o.lat) or math.isnan(o.lng):
            raise ValueError(
                f"Order {o.id} has NaN coordinates: lat={o.lat}, lng={o.lng}"
            )
        if math.isinf(o.lat) or math.isinf(o.lng):
            raise ValueError(
                f"Order {o.id} has infinite coordinates: lat={o.lat}, lng={o.lng}"
            )

    # Check for duplicate coordinates (warn, don't fail – could be same building)
    seen: dict[tuple[float, float], str] = {}
    for o in orders:
        key = (round(o.lat, 6), round(o.lng, 6))
        if key in seen:
            # Add tiny jitter so graph stays valid
            o.lat += random.uniform(-0.0001, 0.0001)
            o.lng += random.uniform(-0.0001, 0.0001)
        seen[key] = o.id


# ---------------------------------------------------------------------------
# Traffic / realism weight multiplier
# ---------------------------------------------------------------------------

def _traffic_multiplier(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Simulate a realistic traffic/road-condition multiplier.

    Real roads are ~1.3–1.6× longer than straight-line Haversine.
    We add a small pseudo-random deterministic factor based on coordinates
    so the same edge always gets the same weight (reproducible).
    """
    # Road detour factor: straight-line distances underestimate real roads
    ROAD_FACTOR = 1.35

    # Deterministic pseudo-random traffic jitter based on coordinate hash
    seed = abs(hash((round(lat1, 4), round(lng1, 4),
                     round(lat2, 4), round(lng2, 4))))
    jitter = 1.0 + (seed % 100) / 500.0  # 0–20% additional variation
    return ROAD_FACTOR * jitter


# ---------------------------------------------------------------------------
# Graph construction
# ---------------------------------------------------------------------------

def build_graph(orders: list[Order], use_osrm: bool = False) -> nx.Graph:
    """
    Build a fully-connected weighted graph from a list of orders.

    Edge weights are Haversine distances in km, multiplied by a
    realistic road-distance factor. If use_osrm is True, attempts to
    use OSRM public API for real road distances (falling back to Haversine on error).
    """
    if not orders:
        return nx.Graph()

    _validate_order_coordinates(orders)

    G = nx.Graph()
    for order in orders:
        G.add_node(order.id, lat=order.lat, lng=order.lng)

    # If OSRM is requested, we can use the distance matrix API
    if use_osrm and len(orders) <= 100:
        coords = ";".join([f"{o.lng},{o.lat}" for o in orders])
        osrm_url = f"http://router.project-osrm.org/table/v1/driving/{coords}?annotations=distance"
        try:
            # We use a short timeout as public OSRM can be flaky
            with httpx.Client(timeout=3.0) as client:
                resp = client.get(osrm_url)
                if resp.status_code == 200:
                    data = resp.json()
                    distances = data.get("distances", [])
                    for i, o1 in enumerate(orders):
                        for j, o2 in enumerate(orders):
                            if i < j:
                                # OSRM returns meters, we convert to km
                                dist_km = distances[i][j] / 1000.0
                                G.add_edge(o1.id, o2.id, weight=round(dist_km, 4))
                    return G
        except Exception as e:
            # Fallback to Haversine
            pass

    for i, o1 in enumerate(orders):
        for o2 in orders[i + 1:]:
            raw_dist = _haversine(o1.lat, o1.lng, o2.lat, o2.lng)
            multiplier = _traffic_multiplier(o1.lat, o1.lng, o2.lat, o2.lng)
            dist = raw_dist * multiplier
            G.add_edge(o1.id, o2.id, weight=round(dist, 4))

    return G


# ---------------------------------------------------------------------------
# Distance helpers (cached)
# ---------------------------------------------------------------------------

class _DistanceMatrix:
    """Pre-compute and cache all pairwise shortest-path distances."""

    def __init__(self, G: nx.Graph) -> None:
        self._cache: dict[tuple[str, str], float] = {}
        # For a complete graph Dijkstra == direct edge, but this
        # keeps correctness if the graph were sparse.
        lengths = dict(nx.all_pairs_dijkstra_path_length(G, weight="weight"))
        for src, targets in lengths.items():
            for tgt, d in targets.items():
                self._cache[(src, tgt)] = d

    def get(self, a: str, b: str) -> float:
        return self._cache.get((a, b), float("inf"))


def _total_route_distance(dm: _DistanceMatrix, route: list[str]) -> float:
    """Compute total distance of a route using the distance matrix."""
    total = 0.0
    for i in range(len(route) - 1):
        total += dm.get(route[i], route[i + 1])
    return total


# ---------------------------------------------------------------------------
# MST lower-bound for B&B pruning
# ---------------------------------------------------------------------------

def _mst_lower_bound(dm: _DistanceMatrix, remaining: set[str], current: str) -> float:
    """
    Compute a Minimum Spanning Tree lower bound for the remaining nodes.

    This gives a tighter pruning bound than just current cost.
    """
    if not remaining:
        return 0.0

    # Minimum edge from current to any remaining node
    min_entry = min(dm.get(current, n) for n in remaining)

    # Prim's MST on remaining nodes
    if len(remaining) <= 1:
        return min_entry

    nodes = list(remaining)
    in_mst = {nodes[0]}
    mst_cost = 0.0

    while len(in_mst) < len(nodes):
        best_edge = float("inf")
        best_node = None
        for u in in_mst:
            for v in nodes:
                if v not in in_mst:
                    d = dm.get(u, v)
                    if d < best_edge:
                        best_edge = d
                        best_node = v
        if best_node is None:
            break
        in_mst.add(best_node)
        mst_cost += best_edge

    return min_entry + mst_cost


# ---------------------------------------------------------------------------
# TSP solvers
# ---------------------------------------------------------------------------

def _tsp_branch_and_bound(dm: _DistanceMatrix, nodes: list[str]) -> list[str]:
    """
    Solve TSP for a set of nodes (≤ 15) using tiered strategies:

    For n ≤ 1  : trivial
    For n ≤ 8  : exact B&B with MST lower-bound pruning
    For 9–15   : nearest-neighbour heuristic + 2-opt + Or-opt local search
    """
    n = len(nodes)

    if n <= 1:
        return list(nodes)

    if n == 2:
        return list(nodes)

    if n <= 8:
        return _exact_bb(dm, nodes)

    # Greedy nearest-neighbour + 2-opt + Or-opt for >8 nodes
    route = _greedy_nearest_neighbour(dm, nodes)
    route = _two_opt_improve(dm, route)
    route = _or_opt_improve(dm, route)
    return route


def _exact_bb(dm: _DistanceMatrix, nodes: list[str]) -> list[str]:
    """
    Exact branch-and-bound with MST lower-bound pruning.

    Uses MST-based bounds for tighter pruning than simple cost comparison.
    """
    best_dist = float("inf")
    best_route: list[str] = list(nodes)

    # Seed with nearest-neighbour to get a good initial upper bound
    nn_route = _greedy_nearest_neighbour(dm, nodes)
    best_dist = _total_route_distance(dm, nn_route)
    best_route = nn_route[:]

    def _search(path: list[str], remaining: set[str], cost: float) -> None:
        nonlocal best_dist, best_route

        # Prune: current cost already exceeds best
        if cost >= best_dist:
            return

        if not remaining:
            if cost < best_dist:
                best_dist = cost
                best_route = path[:]
            return

        # MST lower-bound pruning
        lb = cost + _mst_lower_bound(dm, remaining, path[-1])
        if lb >= best_dist:
            return

        current = path[-1]
        # Sort remaining by distance for better pruning
        for nxt in sorted(remaining, key=lambda x: dm.get(current, x)):
            edge = dm.get(current, nxt)
            new_cost = cost + edge
            if new_cost < best_dist:
                path.append(nxt)
                remaining.remove(nxt)
                _search(path, remaining, new_cost)
                remaining.add(nxt)
                path.pop()

    # Try each node as starting point
    for start in nodes:
        others = set(nodes) - {start}
        _search([start], others, 0.0)

    return best_route


def _greedy_nearest_neighbour(dm: _DistanceMatrix, nodes: list[str]) -> list[str]:
    """Build a route using the nearest-neighbour heuristic from the best start."""
    best_route: list[str] = []
    best_dist = float("inf")

    for start_node in nodes:
        unvisited = set(nodes)
        current = start_node
        route = [current]
        unvisited.remove(current)

        while unvisited:
            nearest = min(unvisited, key=lambda nd: dm.get(current, nd))
            route.append(nearest)
            unvisited.remove(nearest)
            current = nearest

        d = _total_route_distance(dm, route)
        if d < best_dist:
            best_dist = d
            best_route = route

    return best_route


def _two_opt_improve(dm: _DistanceMatrix, route: list[str]) -> list[str]:
    """Improve a route using 2-opt swaps until no further improvement."""
    improved = True
    best = route[:]
    best_dist = _total_route_distance(dm, best)

    while improved:
        improved = False
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                new_route = best[:i] + best[i: j + 1][::-1] + best[j + 1:]
                new_dist = _total_route_distance(dm, new_route)
                if new_dist < best_dist - 1e-9:
                    best = new_route
                    best_dist = new_dist
                    improved = True
                    break
            if improved:
                break

    return best


def _or_opt_improve(dm: _DistanceMatrix, route: list[str]) -> list[str]:
    """
    Improve a route using Or-opt moves.

    Or-opt removes a segment of 1–3 consecutive nodes and reinserts
    it at the best position — often finds improvements that 2-opt misses.
    """
    best = route[:]
    best_dist = _total_route_distance(dm, best)
    improved = True

    while improved:
        improved = False
        for seg_len in (1, 2, 3):
            for i in range(len(best) - seg_len):
                segment = best[i: i + seg_len]
                remainder = best[:i] + best[i + seg_len:]

                for j in range(len(remainder) + 1):
                    candidate = remainder[:j] + segment + remainder[j:]
                    d = _total_route_distance(dm, candidate)
                    if d < best_dist - 1e-9:
                        best = candidate
                        best_dist = d
                        improved = True
                        break
                if improved:
                    break
            if improved:
                break

    return best


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_van_route(orders: list[Order]) -> tuple[list[str], float]:
    """
    Given a list of orders for one van, compute the optimal route.

    Returns (ordered list of order ids, total distance in km).
    Raises ValueError for invalid inputs.
    """
    if not orders:
        return [], 0.0

    if len(orders) == 1:
        return [orders[0].id], 0.0

    G = build_graph(orders, use_osrm=True)
    dm = _DistanceMatrix(G)
    node_ids = [o.id for o in orders]
    optimal_route = _tsp_branch_and_bound(dm, node_ids)
    total_distance = _total_route_distance(dm, optimal_route)

    return optimal_route, round(total_distance, 2)
