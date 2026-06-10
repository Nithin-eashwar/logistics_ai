import pytest
from backend.models.schemas import Order
from backend.algorithms.triage import sort_orders_by_priority
from backend.algorithms.knapsack import assign_orders_to_vans

def test_triage_sorting():
    orders = [
        Order(id="1", lat=0, lng=0, weight=10, priority=5),
        Order(id="2", lat=0, lng=0, weight=20, priority=10),
        Order(id="3", lat=0, lng=0, weight=5, priority=5)
    ]
    sorted_orders = sort_orders_by_priority(orders)
    assert sorted_orders[0].id == "2" # Highest priority
    assert sorted_orders[1].id == "1" # Tie-break by weight (heavier first)
    assert sorted_orders[2].id == "3"

def test_knapsack_capacity():
    orders = [
        Order(id="1", lat=0, lng=0, weight=30, priority=5),
        Order(id="2", lat=0, lng=0, weight=25, priority=5),
    ]
    vans = assign_orders_to_vans(orders, max_weight=50)
    assert len(vans) == 2
    assert sum(o.weight for o in vans[0]) <= 50
    assert sum(o.weight for o in vans[1]) <= 50
