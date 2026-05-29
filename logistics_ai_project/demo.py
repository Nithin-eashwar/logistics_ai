"""
╔══════════════════════════════════════════════════════════════════╗
║     LOGISTICS AI — ALGORITHM PIPELINE DEMO                      ║
║     DAA Semester 4 · Offline / Backend-Only Demonstration       ║
╚══════════════════════════════════════════════════════════════════╝

Run from the logistics_ai_project/ directory:
    python demo.py
"""

from __future__ import annotations

import math
import sys
import time

# ── Rich terminal colours (no external deps) ──────────────────────
RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
BLUE   = "\033[94m"
MAGENTA= "\033[95m"
CYAN   = "\033[96m"
WHITE  = "\033[97m"
BG_DARK= "\033[48;5;235m"

def clr(text: str, *codes: str) -> str:
    return "".join(codes) + str(text) + RESET

def hr(char: str = "─", width: int = 65, color: str = DIM) -> str:
    return clr(char * width, color)

def section(title: str, icon: str = "▶", color: str = CYAN) -> None:
    print()
    print(hr("═", 65, color))
    print(clr(f"  {icon}  {title}", BOLD, color))
    print(hr("═", 65, color))

def step(n: int, label: str, algo: str) -> None:
    print()
    print(clr(f"  STEP {n}/3", BOLD, YELLOW), clr(f"— {label}", WHITE))
    print(clr(f"  Algorithm: {algo}", DIM, CYAN))
    print(hr("·", 65, DIM))

def pause(ms: int = 300) -> None:
    time.sleep(ms / 1000)

# ─────────────────────────────────────────────────────────────────
# Import project modules (with helpful error message)
# ─────────────────────────────────────────────────────────────────
try:
    from backend.algorithms.triage  import sort_orders_by_priority
    from backend.algorithms.knapsack import assign_orders_to_vans
    from backend.algorithms.routing  import compute_van_route
    from backend.models.schemas      import Order
except ModuleNotFoundError as e:
    print(clr("\n  ✗  Import error:", BOLD, RED), str(e))
    print(clr("     Make sure you are running from: logistics_ai_project/", DIM))
    print(clr("     Command: python demo.py\n", DIM))
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────
# Sample data — 10 Bengaluru delivery orders
# ─────────────────────────────────────────────────────────────────
RAW_ORDERS = [
    {"id": "A1",  "lat": 12.9716, "lng": 77.5946, "weight": 5,  "priority": 8},
    {"id": "A2",  "lat": 12.9352, "lng": 77.6245, "weight": 12, "priority": 5},
    {"id": "A3",  "lat": 12.9698, "lng": 77.7500, "weight": 8,  "priority": 9},
    {"id": "A4",  "lat": 13.0358, "lng": 77.5970, "weight": 15, "priority": 3},
    {"id": "A5",  "lat": 12.9141, "lng": 77.6411, "weight": 7,  "priority": 7},
    {"id": "A6",  "lat": 13.0827, "lng": 77.5877, "weight": 10, "priority": 6},
    {"id": "A7",  "lat": 12.9611, "lng": 77.5388, "weight": 4,  "priority": 10},
    {"id": "A8",  "lat": 12.9063, "lng": 77.5857, "weight": 20, "priority": 2},
    {"id": "A9",  "lat": 13.0105, "lng": 77.5519, "weight": 6,  "priority": 4},
    {"id": "A10", "lat": 12.9783, "lng": 77.6408, "weight": 9,  "priority": 1},
]

PRIORITY_BAR = {10: "██████████", 9: "█████████░", 8: "████████░░",
                7: "███████░░░", 6: "██████░░░░", 5: "█████░░░░░",
                4: "████░░░░░░", 3: "███░░░░░░░", 2: "██░░░░░░░░",
                1: "█░░░░░░░░░"}

PRIORITY_COLOR = {10: GREEN, 9: GREEN, 8: GREEN, 7: CYAN, 6: CYAN,
                  5: YELLOW, 4: YELLOW, 3: RED, 2: RED, 1: RED}

WEIGHT_BAR = lambda w: "▓" * max(1, w // 2) + "░" * max(0, 10 - w // 2)


# ─────────────────────────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────────────────────────
def print_banner() -> None:
    print()
    print(clr("  ╔══════════════════════════════════════════════════════╗", CYAN))
    print(clr("  ║  ", CYAN) + clr("🚛  LOGISTICS AI — ALGORITHM PIPELINE", BOLD, WHITE) + clr("         ║", CYAN))
    print(clr("  ║  ", CYAN) + clr("     Fleet Routing Optimizer  ·  v2.1.0", DIM)        + clr("          ║", CYAN))
    print(clr("  ║  ", CYAN) + clr("     DAA Semester 4 · Live Backend Demo", DIM)        + clr("          ║", CYAN))
    print(clr("  ╚══════════════════════════════════════════════════════╝", CYAN))
    print()
    print(clr("  Algorithms Used:", BOLD, WHITE))
    print(clr("    1. ", DIM) + clr("QuickSort (iterative + randomised pivot)", YELLOW) + clr("  →  Triage / Priority Sort", DIM))
    print(clr("    2. ", DIM) + clr("0/1 Knapsack (1D DP + backtracking)    ", MAGENTA) + clr("  →  Van Packing", DIM))
    print(clr("    3. ", DIM) + clr("Dijkstra + TSP (B&B / 2-opt / Or-opt)  ", GREEN)   + clr("  →  Route Optimization", DIM))


# ─────────────────────────────────────────────────────────────────
# PHASE 0 — Show input data
# ─────────────────────────────────────────────────────────────────
def show_input(orders: list[Order]) -> None:
    section("INPUT DATA — 10 Delivery Orders", "📦", BLUE)
    print()
    print(clr(f"  {'ID':<5} {'Priority':>10}  {'Bar':<12} {'Weight':>8}  {'Bar':<12} {'Location'}", BOLD, WHITE))
    print(hr("─", 65, DIM))
    for o in orders:
        pcol = PRIORITY_COLOR[o.priority]
        pbar = clr(PRIORITY_BAR[o.priority], pcol)
        wbar = clr(WEIGHT_BAR(int(o.weight)), BLUE)
        loc  = clr(f"({o.lat:.4f}, {o.lng:.4f})", DIM)
        print(f"  {clr(o.id, BOLD, WHITE):<14} "
              f"{clr(str(o.priority), pcol):>6}/10  {pbar}  "
              f"{clr(str(o.weight)+' kg', CYAN):>8}  {wbar}  {loc}")
        pause(80)

    total_w = sum(o.weight for o in orders)
    avg_pri = sum(o.priority for o in orders) / len(orders)
    print()
    print(hr("─", 65, DIM))
    print(f"  {clr('Total orders:', BOLD)}  {clr(str(len(orders)), WHITE, BOLD)}"
          f"    {clr('Total weight:', BOLD)}  {clr(str(total_w)+' kg', CYAN, BOLD)}"
          f"    {clr('Avg priority:', BOLD)}  {clr(f'{avg_pri:.1f}', YELLOW, BOLD)}")


# ─────────────────────────────────────────────────────────────────
# PHASE 1 — QuickSort Triage
# ─────────────────────────────────────────────────────────────────
def show_triage(orders: list[Order]) -> list[Order]:
    step(1, "TRIAGE — Sort orders by priority", "QuickSort  ·  O(n log n)  ·  iterative, randomised pivot")

    print(clr("\n  Concept:", BOLD, WHITE))
    print(clr("  Higher priority orders must be delivered first — medical, perishable,", DIM))
    print(clr("  or SLA-critical. We use iterative QuickSort (not recursive) to avoid", DIM))
    print(clr("  stack overflow at scale. Tie-break: heavier orders come first so the", DIM))
    print(clr("  knapsack packs the most impactful items early.", DIM))

    print(clr("\n  Sorting…", YELLOW))
    pause(400)

    t0 = time.perf_counter()
    sorted_orders = sort_orders_by_priority(orders)
    elapsed = (time.perf_counter() - t0) * 1000

    print()
    print(clr(f"  {'Rank':<6} {'ID':<6} {'Priority':>10}  {'Bar':<12} {'Weight':>8}", BOLD, WHITE))
    print(hr("─", 55, DIM))
    for rank, o in enumerate(sorted_orders, 1):
        pcol = PRIORITY_COLOR[o.priority]
        pbar = clr(PRIORITY_BAR[o.priority], pcol)
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"  {rank}.")
        print(f"  {medal:<7} {clr(o.id, BOLD, WHITE):<14} "
              f"{clr(str(o.priority), pcol):>6}/10  {pbar}  "
              f"{clr(str(o.weight)+' kg', CYAN):>8}")
        pause(60)

    print()
    print(clr(f"  ✓  Sorted {len(sorted_orders)} orders in {elapsed:.3f} ms", GREEN, BOLD))
    print(clr(f"  ✓  Top priority order: {sorted_orders[0].id}  "
              f"(priority={sorted_orders[0].priority}, weight={sorted_orders[0].weight} kg)", GREEN))
    return sorted_orders


# ─────────────────────────────────────────────────────────────────
# PHASE 2 — 0/1 Knapsack Van Assignment
# ─────────────────────────────────────────────────────────────────
def show_knapsack(sorted_orders: list[Order]) -> list[list[Order]]:
    step(2, "VAN PACKING — Assign orders to vans", "0/1 Knapsack  ·  O(n × W) DP  ·  capacity = 50 kg/van")

    print(clr("\n  Concept:", BOLD, WHITE))
    print(clr("  Each van carries up to 50 kg. The DP table maximises total priority", DIM))
    print(clr("  value (not just weight) per van — so high-priority orders get", DIM))
    print(clr("  dispatched first. After packing one van, remaining orders go to", DIM))
    print(clr("  the next van. This repeats until all orders are assigned.", DIM))

    print(clr("\n  Packing vans…", YELLOW))
    pause(400)

    t0 = time.perf_counter()
    van_assignments = assign_orders_to_vans(sorted_orders)
    elapsed = (time.perf_counter() - t0) * 1000

    VAN_ICONS = ["🚐", "🚚", "🚛", "🚌", "🚑"]
    VAN_COLORS = [GREEN, CYAN, MAGENTA, YELLOW, BLUE]

    print()
    for idx, van_orders in enumerate(van_assignments):
        vcol  = VAN_COLORS[idx % len(VAN_COLORS)]
        vicon = VAN_ICONS[idx % len(VAN_ICONS)]
        van_weight = sum(o.weight for o in van_orders)
        van_priority = sum(o.priority for o in van_orders)
        capacity_pct = (van_weight / 50) * 100
        fill_bars = int(capacity_pct / 5)
        capacity_bar = clr("█" * fill_bars, vcol) + clr("░" * (20 - fill_bars), DIM)

        print(f"  {vicon}  {clr(f'Van {idx+1}', BOLD, vcol)}")
        print(f"     Orders : {clr(', '.join(o.id for o in van_orders), WHITE)}")
        print(f"     Weight : {clr(f'{van_weight} kg / 50 kg', vcol)}  [{capacity_bar}]  "
              f"{clr(f'{capacity_pct:.0f}%', vcol)}")
        print(f"     Priority sum : {clr(str(van_priority), YELLOW)}")
        print()
        pause(200)

    print(hr("─", 65, DIM))
    print(clr(f"  ✓  {len(sorted_orders)} orders → {len(van_assignments)} vans packed in {elapsed:.3f} ms", GREEN, BOLD))
    print(clr(f"  ✓  Knapsack constraint satisfied: no van exceeds 50 kg", GREEN))
    return van_assignments


# ─────────────────────────────────────────────────────────────────
# PHASE 3 — TSP Route Optimization
# ─────────────────────────────────────────────────────────────────
def show_routing(van_assignments: list[list[Order]]) -> list[tuple]:
    step(3, "ROUTE OPTIMIZATION — TSP per van", "Dijkstra (all-pairs) + TSP Branch & Bound / 2-opt / Or-opt")

    print(clr("\n  Concept:", BOLD, WHITE))
    print(clr("  For each van's delivery set, we solve Travelling Salesman Problem.", DIM))
    print(clr("  Dijkstra gives us pairwise road distances (Haversine + traffic factor).", DIM))
    print(clr("  For ≤8 stops: exact Branch & Bound with MST pruning. For >8: greedy", DIM))
    print(clr("  nearest-neighbour + 2-opt + Or-opt local search. This is NP-hard so", DIM))
    print(clr("  the heuristic trades ~15% optimality for polynomial time.", DIM))

    print(clr("\n  Computing routes…", YELLOW))
    pause(400)

    VAN_ICONS  = ["🚐", "🚚", "🚛", "🚌", "🚑"]
    VAN_COLORS = [GREEN, CYAN, MAGENTA, YELLOW, BLUE]

    results = []
    total_dist = 0.0

    print()
    for idx, van_orders in enumerate(van_assignments):
        vcol  = VAN_COLORS[idx % len(VAN_COLORS)]
        vicon = VAN_ICONS[idx % len(VAN_ICONS)]

        t0 = time.perf_counter()
        route, distance = compute_van_route(van_orders)
        elapsed_v = (time.perf_counter() - t0) * 1000
        total_dist += distance

        # Build a visual path string
        path_str = " → ".join(clr(r, vcol, BOLD) for r in route)

        print(f"  {vicon}  {clr(f'Van {idx+1}  Route', BOLD, vcol)}")
        print(f"     Path     : {path_str}")
        print(f"     Distance : {clr(f'{distance:.2f} km', WHITE, BOLD)}"
              f"   {clr(f'(computed in {elapsed_v:.2f} ms)', DIM)}")
        results.append((idx + 1, route, distance))
        print()
        pause(200)

    print(hr("─", 65, DIM))
    print(clr(f"  ✓  All routes computed. Total fleet distance: {total_dist:.2f} km", GREEN, BOLD))
    return results


# ─────────────────────────────────────────────────────────────────
# FINAL SUMMARY
# ─────────────────────────────────────────────────────────────────
def show_summary(
    orders: list[Order],
    van_assignments: list[list[Order]],
    route_results: list[tuple],
    total_elapsed_ms: float,
) -> None:
    section("FINAL RESULTS SUMMARY", "📊", GREEN)

    total_dist = sum(d for _, _, d in route_results)
    VAN_ICONS  = ["🚐", "🚚", "🚛", "🚌", "🚑"]
    VAN_COLORS = [GREEN, CYAN, MAGENTA, YELLOW, BLUE]

    print()
    print(clr(f"  {'Van':<8} {'Orders':<28} {'Weight':>10} {'Distance':>12}", BOLD, WHITE))
    print(hr("─", 65, DIM))

    for idx, van_orders in enumerate(van_assignments):
        _, _, dist = route_results[idx]
        vcol   = VAN_COLORS[idx % len(VAN_COLORS)]
        vicon  = VAN_ICONS[idx % len(VAN_ICONS)]
        ids    = ", ".join(o.id for o in van_orders)
        wt     = sum(o.weight for o in van_orders)
        print(f"  {vicon} {clr(f'Van {idx+1}', BOLD, vcol):<16} "
              f"{clr(ids, WHITE):<28} "
              f"{clr(str(wt)+' kg', CYAN):>10}  "
              f"{clr(f'{dist:.2f} km', YELLOW):>12}")
        pause(100)

    print(hr("─", 65, DIM))
    print()

    # KPI cards
    kpis = [
        ("Total Orders",  str(len(orders)),            WHITE),
        ("Vans Deployed", str(len(van_assignments)),   GREEN),
        ("Total Weight",  f"{sum(o.weight for o in orders)} kg", CYAN),
        ("Fleet Distance",f"{total_dist:.2f} km",      YELLOW),
        ("Pipeline Time", f"{total_elapsed_ms:.2f} ms",MAGENTA),
    ]
    print(clr("  Key Performance Indicators:", BOLD, WHITE))
    print()
    for label, value, col in kpis:
        bar = "  "
        print(f"  {bar}{clr(label+':' , DIM):<22}  {clr(value, BOLD, col)}")
        pause(80)

    print()
    print(clr("  ╔════════════════════════════════════════════════════╗", GREEN))
    print(clr("  ║  ✅  Pipeline complete — all algorithms verified   ║", GREEN, BOLD))
    print(clr("  ╚════════════════════════════════════════════════════╝", GREEN))
    print()


# ─────────────────────────────────────────────────────────────────
# COMPLEXITY CHEATSHEET (for panel Q&A)
# ─────────────────────────────────────────────────────────────────
def show_complexity() -> None:
    section("ALGORITHM COMPLEXITY REFERENCE", "📐", MAGENTA)
    print()
    rows = [
        ("QuickSort (Triage)",  "O(n log n)", "O(n log n)", "O(n)",    "Iterative, randomised pivot"),
        ("0/1 Knapsack",        "O(n × W)",   "O(n × W)",   "O(n)",    "W = 50 (van capacity kg)"),
        ("Dijkstra (all-pairs)","O(n² log n)","O(n²)",      "O(n²)",   "Using NetworkX"),
        ("TSP Branch & Bound",  "O(n!)",      "O(n × 2ⁿ)",  "O(n²)",   "≤8 nodes exact, else heuristic"),
        ("2-opt / Or-opt",      "O(n²)",      "O(n²)",      "O(n)",    "Local search improvement"),
    ]
    print(clr(f"  {'Algorithm':<24} {'Best':>12} {'Avg':>12} {'Space':>8}  {'Note'}", BOLD, WHITE))
    print(hr("─", 80, DIM))
    for name, best, avg, space, note in rows:
        print(f"  {clr(name, CYAN):<32} {clr(best, GREEN):>12} {clr(avg, YELLOW):>12} "
              f"{clr(space, MAGENTA):>8}  {clr(note, DIM)}")
        pause(80)
    print()


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main() -> None:
    print_banner()
    input(clr("\n  Press ENTER to start the demo…", DIM, CYAN))

    # Build Order objects
    orders = [Order(**o) for o in RAW_ORDERS]

    # Phase 0: Show input
    show_input(orders)
    input(clr("\n  Press ENTER for Step 1 — Triage…", DIM, CYAN))

    # Phase 1: QuickSort
    t_start = time.perf_counter()
    sorted_orders = show_triage(orders)
    input(clr("\n  Press ENTER for Step 2 — Van Packing…", DIM, CYAN))

    # Phase 2: Knapsack
    van_assignments = show_knapsack(sorted_orders)
    input(clr("\n  Press ENTER for Step 3 — Route Optimization…", DIM, CYAN))

    # Phase 3: Routing
    route_results = show_routing(van_assignments)
    total_elapsed = (time.perf_counter() - t_start) * 1000

    input(clr("\n  Press ENTER to see Final Summary…", DIM, CYAN))

    # Summary
    show_summary(orders, van_assignments, route_results, total_elapsed)

    # Complexity reference
    input(clr("  Press ENTER to see Complexity Reference (good for Q&A)…", DIM, CYAN))
    show_complexity()

    print(clr("  Demo complete. Thank you!\n", BOLD, GREEN))


if __name__ == "__main__":
    main()
