"""Clustering module: K-Means for spatial grouping of orders."""

from __future__ import annotations

import math
import random

from backend.models.schemas import Order


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


def kmeans_cluster(orders: list[Order], k: int, max_iters: int = 100) -> list[list[Order]]:
    """
    Cluster orders into k spatial zones using K-Means (Lloyd's algorithm).
    
    This ensures that orders packed into the same van are geographically close,
    solving the 'Cluster First, Route Second' flaw in naive logistics pipelines.
    """
    if not orders:
        return []
    if k <= 1:
        return [list(orders)]
    if k >= len(orders):
        return [[o] for o in orders]

    # Initialize centroids randomly from existing points
    centroids = random.sample([(o.lat, o.lng) for o in orders], k)
    
    clusters: list[list[Order]] = []
    
    for _ in range(max_iters):
        clusters = [[] for _ in range(k)]
        
        # Assignment step
        for o in orders:
            best_k = 0
            best_dist = float("inf")
            for i, (c_lat, c_lng) in enumerate(centroids):
                dist = _haversine(o.lat, o.lng, c_lat, c_lng)
                if dist < best_dist:
                    best_dist = dist
                    best_k = i
            clusters[best_k].append(o)
            
        # Update step
        new_centroids = []
        for i in range(k):
            if not clusters[i]:
                # Handle empty cluster by picking a random order
                rand_o = random.choice(orders)
                new_centroids.append((rand_o.lat, rand_o.lng))
            else:
                avg_lat = sum(o.lat for o in clusters[i]) / len(clusters[i])
                avg_lng = sum(o.lng for o in clusters[i]) / len(clusters[i])
                new_centroids.append((avg_lat, avg_lng))
                
        # Check convergence
        diff = sum(
            _haversine(c1[0], c1[1], c2[0], c2[1]) 
            for c1, c2 in zip(centroids, new_centroids)
        )
        if diff < 1e-6:
            break
            
        centroids = new_centroids
        
    # Return non-empty clusters
    return [c for c in clusters if c]
