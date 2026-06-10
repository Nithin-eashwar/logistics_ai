"""Knapsack module: 0/1 Knapsack to assign orders to vans."""

from __future__ import annotations

import logging

import math

from backend.models.schemas import Order
from backend.algorithms.clustering import kmeans_cluster

logger = logging.getLogger(__name__)

MAX_WEIGHT_PER_VAN = 50


def _validate_orders(orders: list[Order]) -> None:
    """Validate orders before knapsack processing."""
    for o in orders:
        if o.weight <= 0:
            raise ValueError(f"Order {o.id} has invalid weight: {o.weight}")
        if o.priority < 1:
            raise ValueError(f"Order {o.id} has invalid priority: {o.priority}")


def _knapsack_01(orders: list[Order], capacity: int) -> list[Order]:
    """
    Classic 0/1 knapsack using dynamic programming.

    Value  = order priority
    Weight = order weight (ceiling-rounded to integer for DP table)
    Returns the list of orders that fit within *capacity*
    while maximising total priority value.

    Uses space-efficient 1D DP array — O(capacity) memory instead of
    O(n * capacity).
    """
    if not orders:
        return []

    if capacity <= 0:
        raise ValueError(f"Van capacity must be positive, got {capacity}")

    n = len(orders)
    weights = [max(1, int(o.weight + 0.999)) for o in orders]  # ceil, min 1
    values = [o.priority for o in orders]

    # Guard: if every single order exceeds capacity on its own, return empty
    if all(w > capacity for w in weights):
        return []

    # Space-efficient 1D DP — O(capacity) memory
    dp = [0] * (capacity + 1)
    # Track which items are selected (needed for backtracking)
    keep = [[False] * (capacity + 1) for _ in range(n)]

    for i in range(n):
        w_i = weights[i]
        v_i = values[i]
        # Traverse backwards to avoid using same item twice
        for w in range(capacity, w_i - 1, -1):
            if dp[w - w_i] + v_i > dp[w]:
                dp[w] = dp[w - w_i] + v_i
                keep[i][w] = True

    # Backtrack to find selected items
    selected: list[Order] = []
    w = capacity
    for i in range(n - 1, -1, -1):
        if keep[i][w]:
            selected.append(orders[i])
            w -= weights[i]

    logger.debug(
        "Knapsack selected %d/%d orders (%.1f/%.0f kg, %d priority)",
        len(selected),
        n,
        sum(o.weight for o in selected),
        capacity,
        sum(o.priority for o in selected),
    )

    return selected


def assign_orders_to_vans(
    orders: list[Order],
    max_weight: int = MAX_WEIGHT_PER_VAN,
) -> list[list[Order]]:
    """
    Assign orders to vans using K-Means spatial clustering followed by repeated 0/1 knapsack.

    Each van has a maximum payload of *max_weight* kg.
    Returns a list of order-groups, one per van.
    """
    if not orders:
        return []

    _validate_orders(orders)

    # Calculate optimal number of clusters (vans)
    total_weight = sum(o.weight for o in orders)
    k = max(1, int(math.ceil(total_weight / max_weight)))

    # Phase 1: Spatial Clustering
    # Group orders that are geographically close so vans don't travel across the city
    clusters = kmeans_cluster(orders, k)
    vans: list[list[Order]] = []

    # Phase 2: Knapsack packing per cluster
    for cluster in clusters:
        remaining = list(cluster)
        
        while remaining:
            selected = _knapsack_01(remaining, max_weight)

        if not selected:
            # Edge case: the lightest remaining order still exceeds capacity.
            # Force-assign orders one-by-one from lightest to heaviest.
            remaining.sort(key=lambda o: o.weight)
            selected = [remaining[0]]
            logger.warning(
                "Order %s (%.1f kg) exceeds van capacity %d kg — "
                "force-assigned to its own van.",
                remaining[0].id,
                remaining[0].weight,
                max_weight,
            )

        vans.append(selected)
        selected_ids = {o.id for o in selected}
        remaining = [o for o in remaining if o.id not in selected_ids]

    logger.info(
        "Assigned %d orders across %d vans (max %.0f kg each)",
        len(orders),
        len(vans),
        max_weight,
    )

    return vans
