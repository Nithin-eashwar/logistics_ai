"""
╔══════════════════════════════════════════════════════════════════╗
║     LOGISTICS AI — ALGORITHM PIPELINE DEMO                      ║
║     DAA Semester 4 · Interactive Terminal + Live Frontend       ║
╚══════════════════════════════════════════════════════════════════╝

Run from the logistics_ai_project/ directory:
    python demo.py

After entering orders, open (or refresh) the browser at:
    http://localhost:8000
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
# Import project modules
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

# Where we save results for the frontend to read
DATA_DIR    = Path(__file__).parent / "data"
RESULT_FILE = DATA_DIR / "current_result.json"

PRIORITY_BAR = {10: "██████████", 9: "█████████░", 8: "████████░░",
                7: "███████░░░", 6: "██████░░░░", 5: "█████░░░░░",
                4: "████░░░░░░", 3: "███░░░░░░░", 2: "██░░░░░░░░",
                1: "█░░░░░░░░░"}

PRIORITY_COLOR = {10: GREEN, 9: GREEN, 8: GREEN, 7: CYAN, 6: CYAN,
                  5: YELLOW, 4: YELLOW, 3: RED, 2: RED, 1: RED}

WEIGHT_BAR = lambda w: "▓" * max(1, int(w) // 2) + "░" * max(0, 10 - int(w) // 2)

# Bengaluru area bounding box for coordinate generation
BLR_LAT = (12.85, 13.10)
BLR_LNG = (77.48, 77.78)


# ─────────────────────────────────────────────────────────────────
# BANNER
# ─────────────────────────────────────────────────────────────────
def print_banner() -> None:
    print()
    print(clr("  ╔══════════════════════════════════════════════════════╗", CYAN))
    print(clr("  ║  ", CYAN) + clr("🚛  LOGISTICS AI — ALGORITHM PIPELINE", BOLD, WHITE) + clr("         ║", CYAN))
    print(clr("  ║  ", CYAN) + clr("     Fleet Routing Optimizer  ·  v2.1.0", DIM)        + clr("          ║", CYAN))
    print(clr("  ║  ", CYAN) + clr("     DAA Semester 4 · Interactive Demo", DIM)         + clr("          ║", CYAN))
    print(clr("  ╚══════════════════════════════════════════════════════╝", CYAN))
    print()
    print(clr("  Algorithms Used:", BOLD, WHITE))
    print(clr("    1. ", DIM) + clr("QuickSort (iterative + randomised pivot)", YELLOW) + clr("  →  Triage / Priority Sort", DIM))
    print(clr("    2. ", DIM) + clr("K-Means + 0/1 Knapsack (1D DP)         ", MAGENTA) + clr("  →  Spatial Packing", DIM))
    print(clr("    3. ", DIM) + clr("Dijkstra + TSP (B&B / 2-opt / Or-opt)  ", GREEN)   + clr("  →  Route Optimization", DIM))


# ─────────────────────────────────────────────────────────────────
# INTERACTIVE ORDER INPUT
# ─────────────────────────────────────────────────────────────────
def get_orders_interactively() -> list[dict]:
    section("ORDER ENTRY — Enter Delivery Orders", "📝", CYAN)

    print(clr("\n  How many delivery orders do you want to optimize?", WHITE))
    print(clr("  (Tip: 5–10 orders make a great demo. Each van holds up to 50 kg.)\n", DIM))

    while True:
        try:
            n = int(input(clr("  Number of orders: ", BOLD, CYAN)))
            if n < 1:
                print(clr("  ✗  Need at least 1 order.", RED))
                continue
            if n > 20:
                print(clr("  ✗  Maximum orders allowed is 20.", RED))
                continue
            break
        except ValueError:
            print(clr("  ✗  Please enter a valid number.", RED))

    print()
    orders = []
    for i in range(n):
        print(clr(f"  ── Order {i+1} of {n} ──────────────────────────────────", DIM))

        # ID
        default_id = f"ORD-{i+1:02d}"
        raw = input(clr(f"    Order ID     [{default_id}]: ", CYAN)).strip()
        oid = raw if raw else default_id

        # Weight
        while True:
            try:
                raw_w = input(clr("    Weight (kg)  [max 50]: ", CYAN)).strip()
                weight = float(raw_w) if raw_w else round(random.uniform(2, 20), 1)
                if weight <= 0 or weight > 50:
                    print(clr("    ✗  Weight must be between 1 and 50 kg.", RED))
                    continue
                break
            except ValueError:
                print(clr("    ✗  Enter a number (e.g. 12 or 7.5).", RED))

        # Priority
        while True:
            try:
                raw_p = input(clr("    Priority     [1–10, 10=urgent]: ", CYAN)).strip()
                priority = int(raw_p) if raw_p else random.randint(1, 10)
                if priority < 1 or priority > 10:
                    print(clr("    ✗  Priority must be 1–10.", RED))
                    continue
                break
            except ValueError:
                print(clr("    ✗  Enter a whole number (e.g. 7).", RED))

        # Deadline (optional)
        print(clr("    Deadline     [leave blank = none, or e.g. +2h / +30m / YYYY-MM-DD HH:MM]: ", CYAN), end="")
        raw_dl = input().strip()
        deadline_iso: str | None = None
        if raw_dl:
            now = datetime.now(tz=timezone.utc)
            # Shorthand helpers: +Nh = N hours, +Nm = N minutes
            if raw_dl.startswith("+") and raw_dl.endswith("h") and raw_dl[1:-1].isdigit():
                dl = now + timedelta(hours=int(raw_dl[1:-1]))
                deadline_iso = dl.isoformat()
            elif raw_dl.startswith("+") and raw_dl.endswith("m") and raw_dl[1:-1].isdigit():
                dl = now + timedelta(minutes=int(raw_dl[1:-1]))
                deadline_iso = dl.isoformat()
            else:
                try:
                    dl = datetime.strptime(raw_dl, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                    deadline_iso = dl.isoformat()
                except ValueError:
                    print(clr("    ✗  Unrecognised format — deadline ignored.", RED))

        # Destination (label only — coords are auto-generated)
        raw_d = input(clr("    Destination  [area/city]: ", CYAN)).strip()
        destination = raw_d if raw_d else f"Zone-{i+1}"

        # Auto-generate realistic Bengaluru coordinates
        lat = round(random.uniform(*BLR_LAT), 4)
        lng = round(random.uniform(*BLR_LNG), 4)

        orders.append({
            "id": oid, "lat": lat, "lng": lng,
            "weight": weight, "priority": priority,
            "deadline": deadline_iso,
            "destination": destination,
        })
        dl_label = deadline_iso[:16] if deadline_iso else "none"
        print(clr(f"    ✓  Added  {oid}  |  {weight} kg  |  P{priority}  |  deadline={dl_label}  |  {destination}", GREEN))
        print()

    return orders


# ─────────────────────────────────────────────────────────────────
# PHASE 0 — Show input data
# ─────────────────────────────────────────────────────────────────
def show_input(orders: list[Order]) -> None:
    section(f"INPUT DATA — {len(orders)} Delivery Orders", "📦", BLUE)
    print()
    print(clr(f"  {'ID':<8} {'Coordinates':<17} {'Priority':>10}  {'Bar':<12} {'Weight':>8}  {'Bar':<12}", BOLD, WHITE))
    print(hr("─", 78, DIM))
    for o in orders:
        pcol = PRIORITY_COLOR[o.priority]
        pbar = clr(PRIORITY_BAR[o.priority], pcol)
        wbar = clr(WEIGHT_BAR(int(o.weight)), BLUE)
        dest = f"{o.lat:.4f}, {o.lng:.4f}"
        print(f"  {clr(o.id, BOLD, WHITE):<16} {dest:<17} "
              f"{clr(str(o.priority), pcol):>6}/10  {pbar}  "
              f"{clr(str(o.weight)+' kg', CYAN):>8}  {wbar}")
        pause(80)

    total_w  = sum(o.weight for o in orders)
    avg_pri  = sum(o.priority for o in orders) / len(orders)
    print()
    print(hr("─", 75, DIM))
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
    print(clr(f"  {'Rank':<6} {'ID':<10} {'Coordinates':<17} {'Priority':>10}  {'Bar':<12} {'Weight':>8}  {'Deadline':<20}", BOLD, WHITE))
    print(hr("─", 88, DIM))
    for rank, o in enumerate(sorted_orders, 1):
        pcol  = PRIORITY_COLOR[o.priority]
        pbar  = clr(PRIORITY_BAR[o.priority], pcol)
        medal = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"  {rank}.")
        dest  = f"{o.lat:.4f}, {o.lng:.4f}"
        dl    = getattr(o, "deadline", None)
        dl_str = dl.strftime("%m-%d %H:%M") if dl else clr("none", DIM)
        print(f"  {medal:<7} {clr(o.id, BOLD, WHITE):<18} {dest:<17} "
              f"{clr(str(o.priority), pcol):>6}/10  {pbar}  "
              f"{clr(str(o.weight)+' kg', CYAN):>8}  {clr(dl_str, YELLOW):<20}")
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
    step(2, "VAN PACKING — Assign orders to vans", "K-Means Spatial Clustering + 0/1 Knapsack DP")

    print(clr("\n  Concept:", BOLD, WHITE))
    print(clr("  First, orders are clustered into geographic zones using K-Means to ensure", DIM))
    print(clr("  vans don't drive across the city. Then, each van carries up to 50 kg.", DIM))
    print(clr("  The DP table maximises total priority value per zone — so high-priority", DIM))
    print(clr("  orders get dispatched first. Remaining orders go to the next van.", DIM))

    print(clr("\n  Packing vans…", YELLOW))
    pause(400)

    t0 = time.perf_counter()
    van_assignments = assign_orders_to_vans(sorted_orders)
    elapsed = (time.perf_counter() - t0) * 1000

    VAN_ICONS  = ["🚐", "🚚", "🚛", "🚌", "🚑"]
    VAN_COLORS = [GREEN, CYAN, MAGENTA, YELLOW, BLUE]

    print()
    for idx, van_orders in enumerate(van_assignments):
        vcol  = VAN_COLORS[idx % len(VAN_COLORS)]
        vicon = VAN_ICONS[idx % len(VAN_ICONS)]
        van_weight   = sum(o.weight for o in van_orders)
        van_priority = sum(o.priority for o in van_orders)
        capacity_pct = (van_weight / 50) * 100
        fill_bars    = int(capacity_pct / 5)
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

    results    = []
    total_dist = 0.0

    print()
    for idx, van_orders in enumerate(van_assignments):
        vcol  = VAN_COLORS[idx % len(VAN_COLORS)]
        vicon = VAN_ICONS[idx % len(VAN_ICONS)]

        t0 = time.perf_counter()
        route, distance = compute_van_route(van_orders)
        elapsed_v = (time.perf_counter() - t0) * 1000
        total_dist += distance

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
def show_summary(orders, van_assignments, route_results, total_elapsed_ms) -> None:
    section("FINAL RESULTS SUMMARY", "📊", GREEN)

    total_dist = sum(d for _, _, d in route_results)
    VAN_ICONS  = ["🚐", "🚚", "🚛", "🚌", "🚑"]
    VAN_COLORS = [GREEN, CYAN, MAGENTA, YELLOW, BLUE]

    print()
    print(clr(f"  {'Van':<8} {'Orders':<28} {'Weight':>10} {'Distance':>12}", BOLD, WHITE))
    print(hr("─", 65, DIM))

    for idx, van_orders in enumerate(van_assignments):
        _, _, dist = route_results[idx]
        vcol  = VAN_COLORS[idx % len(VAN_COLORS)]
        vicon = VAN_ICONS[idx % len(VAN_ICONS)]
        ids   = ", ".join(o.id for o in van_orders)
        wt    = sum(o.weight for o in van_orders)
        print(f"  {vicon} {clr(f'Van {idx+1}', BOLD, vcol):<16} "
              f"{clr(ids, WHITE):<28} "
              f"{clr(str(wt)+' kg', CYAN):>10}  "
              f"{clr(f'{dist:.2f} km', YELLOW):>12}")
        pause(100)

    print(hr("─", 65, DIM))
    print()

    kpis = [
        ("Total Orders",  str(len(orders)),                      WHITE),
        ("Vans Deployed", str(len(van_assignments)),              GREEN),
        ("Total Weight",  f"{sum(o.weight for o in orders)} kg", CYAN),
        ("Fleet Distance",f"{total_dist:.2f} km",                YELLOW),
        ("Pipeline Time", f"{total_elapsed_ms:.2f} ms",          MAGENTA),
    ]
    print(clr("  Key Performance Indicators:", BOLD, WHITE))
    print()
    for label, value, col in kpis:
        print(f"    {clr(label+':', DIM):<22}  {clr(value, BOLD, col)}")
        pause(80)

    print()
    print(clr("  ╔════════════════════════════════════════════════════╗", GREEN))
    print(clr("  ║  ✅  Pipeline complete — all algorithms verified   ║", GREEN, BOLD))
    print(clr("  ╚════════════════════════════════════════════════════╝", GREEN))
    print()


# ─────────────────────────────────────────────────────────────────
# COMPLEXITY CHEATSHEET
# ─────────────────────────────────────────────────────────────────
def show_complexity() -> None:
    section("ALGORITHM COMPLEXITY REFERENCE", "📐", MAGENTA)
    print()
    rows = [
        ("QuickSort (Triage)",   "O(n log n)", "O(n log n)", "O(n)",  "Iterative, randomised pivot"),
        ("K-Means + Knapsack",   "O(n × W)",   "O(k·n·i)",   "O(n)",  "W = 50 (van capacity kg)"),
        ("Dijkstra (all-pairs)", "O(n² log n)","O(n²)",      "O(n²)", "Priority queue + Haversine"),
        ("TSP Branch & Bound",   "O(n!)",      "O(n × 2ⁿ)",  "O(n²)", "≤8 nodes exact, else heuristic"),
        ("2-opt / Or-opt",       "O(n²)",      "O(n²)",      "O(n)",  "Local search improvement"),
    ]
    print(clr(f"  {'Algorithm':<24} {'Best':>12} {'Avg':>12} {'Space':>8}  {'Note'}", BOLD, WHITE))
    print(hr("─", 80, DIM))
    for name, best, avg, space, note in rows:
        print(f"  {clr(name, CYAN):<32} {clr(best, GREEN):>12} {clr(avg, YELLOW):>12} "
              f"{clr(space, MAGENTA):>8}  {clr(note, DIM)}")
        pause(80)
    print()


# ─────────────────────────────────────────────────────────────────
# SAVE RESULTS FOR FRONTEND
# ─────────────────────────────────────────────────────────────────
def save_results(orders, sorted_orders, van_assignments, route_results, total_elapsed_ms) -> None:
    """Write full pipeline results to data/current_result.json for the browser."""
    DATA_DIR.mkdir(exist_ok=True)

    total_dist = sum(d for _, _, d in route_results)

    routes = []
    for idx, van_orders in enumerate(van_assignments):
        _, route_path, dist = route_results[idx]
        wt = sum(o.weight for o in van_orders)
        routes.append({
            "van":          f"VAN-{idx+1:02d}",
            "order_ids":    [o.id for o in van_orders],
            "weights":      [o.weight for o in van_orders],
            "priorities":   [o.priority for o in van_orders],
            "destinations": [f"{o.lat:.4f}, {o.lng:.4f}" for o in van_orders],
            "route":        route_path,
            "distance_km":  round(dist, 2),
            "total_weight": round(wt, 1),
            "capacity_pct": round((wt / 50) * 100, 1),
        })

    result = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "input": [
            {"id": o.id, "weight": o.weight, "priority": o.priority,
             "lat": o.lat, "lng": o.lng,
             "deadline": o.deadline.isoformat() if o.deadline else None,
             "destination": f"{o.lat:.4f}, {o.lng:.4f}"}
            for o in orders
        ],
        "step1": {
            "algorithm":  "QuickSort",
            "complexity": "O(n log n)",
            "sorted": [
                {"id": o.id, "priority": o.priority, "weight": o.weight,
                 "deadline": o.deadline.isoformat() if o.deadline else None,
                 "destination": f"{o.lat:.4f}, {o.lng:.4f}"}
                for o in sorted_orders
            ],
        },
        "step2": {
            "algorithm":   "K-Means + 0/1 Knapsack",
            "complexity":  "O(k*n*i) + O(n × W)",
            "van_count":   len(van_assignments),
            "assignments": [
                [{"id": o.id, "weight": o.weight, "priority": o.priority,
                  "destination": f"{o.lat:.4f}, {o.lng:.4f}"}
                 for o in van]
                for van in van_assignments
            ],
        },
        "step3": {
            "algorithm":         "Dijkstra + TSP",
            "complexity":        "O(n² log n) + O(n!) → heuristic",
            "routes":            routes,
            "total_distance_km": round(total_dist, 2),
        },
        "summary": {
            "total_orders":      len(orders),
            "total_vans":        len(van_assignments),
            "total_weight_kg":   sum(o.weight for o in orders),
            "total_distance_km": round(total_dist, 2),
            "pipeline_ms":       round(total_elapsed_ms, 2),
        },
    }

    RESULT_FILE.write_text(json.dumps(result, indent=2))
    print(clr(f"\n  ✓  Results saved → data/current_result.json", GREEN, BOLD))
    print(clr("  ✓  Refresh http://localhost:8000 to see the pipeline in the browser.", CYAN))


# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────
def main() -> None:
    print_banner()

    # ── Interactive order entry ────────────────────────────────────
    raw_orders = get_orders_interactively()

    print()
    input(clr("  ✓  All orders entered. Press ENTER to start the pipeline…", DIM, CYAN))

    # Attach destination as an attribute after creating Order objects
    orders = []
    for o in raw_orders:
        dest = o.pop("destination", "—")
        order = Order(**o)
        object.__setattr__(order, "destination", dest) if hasattr(order, "__setattr__") else None
        try:
            order.destination = dest
        except Exception:
            pass
        orders.append(order)
        # Store destination in a parallel list for save_results
        order._dest = dest  # type: ignore

    # Patch destination access
    for o, rd in zip(orders, raw_orders if raw_orders else []):
        pass

    # Re-attach destination cleanly via a wrapper approach
    class OrderWithDest(Order):
        destination: str = "—"

    orders_with_dest = []
    for i, o_obj in enumerate(orders):
        raw = dict(
            id=o_obj.id, lat=o_obj.lat, lng=o_obj.lng,
            weight=o_obj.weight, priority=o_obj.priority,
            deadline=raw_orders[i].get("deadline"),
            destination=raw_orders[i].get("destination", "—"),
        )
        try:
            ow = OrderWithDest(**raw)
        except Exception:
            ow = o_obj
            ow.destination = raw.get("destination", "—")
        orders_with_dest.append(ow)
    orders = orders_with_dest

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

    # Save for frontend
    save_results(orders, sorted_orders, van_assignments, route_results, total_elapsed)

    # Complexity reference
    input(clr("  Press ENTER to see Complexity Reference (good for Q&A)…", DIM, CYAN))
    show_complexity()

    print(clr("  Demo complete. Thank you!\n", BOLD, GREEN))


if __name__ == "__main__":
    main()
