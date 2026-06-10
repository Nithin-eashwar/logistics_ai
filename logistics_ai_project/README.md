# Logistics AI — Algorithm Pipeline

A full-stack, algorithm-driven logistics and fleet routing optimizer built for DAA (Design and Analysis of Algorithms) Semester 4. This project demonstrates the practical application of core computer science algorithms in a real-world logistics and delivery scenario. 

It features an interactive terminal simulation to generate delivery data, which is then processed by a FastAPI backend and visualised in a sleek, real-time frontend dashboard.

## 🚀 Features
- **Interactive Terminal Demo**: Interactively generate and configure delivery orders, assigning weights and priorities.
- **Algorithmic Pipeline**: Processes orders through three distinct algorithmic phases (Triage, Packing, Routing).
- **Live Sync Dashboard**: A beautiful, scanline-themed web dashboard that syncs with the terminal to visualize the exact algorithm execution, van packing efficiencies, and optimized routes.
- **Traffic Simulation**: Utilises the Haversine formula combined with a deterministic traffic multiplier to simulate realistic road distances in Bengaluru.

## 🧠 The Algorithm Pipeline

The project solves the logistics problem using three sequential steps:

### 1. Priority Triage (QuickSort)
- **Algorithm**: Iterative QuickSort (with a randomised pivot).
- **Time Complexity**: `O(n log n)`
- **Purpose**: Sorts incoming orders based on urgency (1-10 priority scale). High-priority (SLA-critical) orders are pushed to the front of the queue to ensure they get assigned to the earliest available vans. Tie-breakers prioritise heavier items.

### 2. Van Packing (0/1 Knapsack)
- **Algorithm**: 0/1 Knapsack (Dynamic Programming with a 1D rolling array).
- **Time Complexity**: `O(n × W)` where `W = 50` (van capacity).
- **Purpose**: Each delivery van has a strict physical capacity of 50 kg. The algorithm packs the van to maximise the *total priority value* of the payload, ensuring the most important items fit perfectly without exceeding the weight limit. Leftover orders are rolled over to the next van until all orders are assigned.

### 3. Route Optimization (Dijkstra + TSP)
- **Algorithm**: Dijkstra (All-pairs shortest path) + TSP Branch & Bound / 2-opt Heuristic.
- **Time Complexity**: `O(n² log n)` for graph building + `O(n!)` (exact) or `O(n²)` (heuristic) for routing.
- **Purpose**: Calculates the absolute shortest driving path for each individual van to visit all its assigned stops. For vans with ≤8 stops, it uses exact Branch & Bound with Minimum Spanning Tree (MST) pruning. For >8 stops, it gracefully falls back to a nearest-neighbour heuristic improved by 2-opt and Or-opt local searches to solve the NP-hard problem in polynomial time.

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.10+ (Recommended: Conda environment)

### Installation

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd logistics_ai_project
   ```

2. **Create and activate a Conda environment** (recommended to avoid `pip` conflicts):
   ```bash
   conda create -n logistics_env python=3.11 -y
   conda activate logistics_env
   ```

3. **Install dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

## 💻 Usage Instructions

Running the project requires two separate terminal windows: one for the interactive data generation, and one for the web server.

### Step 1: Start the Backend/Frontend Server
In your first terminal tab, make sure your environment is activated, then start the FastAPI server:
```bash
conda activate logistics_env
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```
*Note: This server simultaneously runs the API and serves the frontend dashboard.*

### Step 2: Run the Terminal Demo
Open a **new** terminal tab, activate the environment, and run the interactive demo:
```bash
cd logistics_ai_project
conda activate logistics_env
python demo.py
```
Follow the on-screen prompts to input the number of orders (max 20) and configure their weights and priorities. 

### Step 3: View the Dashboard
Once the terminal script completes its execution and saves the results, open your browser and navigate to:
**[http://localhost:8000](http://localhost:8000)**

You will see the pipeline visualised with beautiful UI components detailing exactly how the algorithms performed.

## 📂 Project Structure
- `demo.py`: The interactive CLI application that orchestrates the algorithms and generates output data.
- `backend/algorithms/`: Contains the modular implementations of the sorting, knapsack, and routing algorithms.
- `backend/main.py`: The FastAPI server that exposes the generated results.
- `frontend/index.html`: A Vanilla HTML/CSS/JS frontend with a dark-mode "hacker" aesthetic that fetches and visualises the algorithm output.
- `data/`: Auto-generated directory where `demo.py` saves `current_result.json` for the frontend to read.
