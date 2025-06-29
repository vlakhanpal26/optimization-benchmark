"""
LP-relaxation via CVXPY + Clarabel.
"""

import os, json, time, contextlib
from pathlib import Path
import numpy as np, pandas as pd, cvxpy as cp

ROOT    = Path(os.environ["BENCHMARK_ROOT"]).resolve()
RES_DIR = ROOT / "data" / "results"
INST_DIR = ROOT / "data" / "instances"
RES_DIR.mkdir(parents=True, exist_ok=True)

# ---------- CSV loader ------------------------------------------------------
def _load_csv(stem):
    f = INST_DIR / stem
    demand     = pd.read_csv(f/"demand.csv", header=None).values.flatten()
    capacity   = pd.read_csv(f/"capacity.csv", header=None).values.flatten()
    fixed_cost = pd.read_csv(f/"fixed_cost.csv", header=None).values.flatten()
    ship_cost  = pd.read_csv(f/"ship_cost.csv", header=None).values
    return demand, capacity, fixed_cost, ship_cost
# ---------------------------------------------------------------------------


def solve_lp(lp_file: Path, time_limit: int = 600):
    model_stem  = lp_file.stem
    solver_name = "Clarabel-LP"

    # ---- load data ---------------------------------------------------------
    demand, capacity, fixed_cost, ship_cost = _load_csv(model_stem)
    F, C = len(capacity), len(demand)

    x = cp.Variable((F, C))
    y = cp.Variable(F)
    objective = cp.sum(cp.multiply(ship_cost, x)) + fixed_cost @ y
    cons = [
        cp.sum(x, axis=0) == demand,
        cp.sum(x, axis=1) <= capacity * y,
        x >= 0, y >= 0, y <= 1]
    prob = cp.Problem(cp.Minimize(objective), cons)

    # ---- solve -------------------------------------------------------------
    log_path = RES_DIR / f"{solver_name.lower()}_{model_stem}.log"
    with open(log_path, "w") as lf, contextlib.redirect_stdout(lf):
        t0 = time.perf_counter()
        prob.solve(
            solver="CLARABEL",
            verbose=True,
            max_iter=10_000      # Clarabel accepts this
            # Clarabel currently has **no** built-in wall-clock time limit
        )
        t1 = time.perf_counter()

    result = {
        "solver"   : solver_name,
        "model"    : model_stem,
        "status"   : prob.status,
        "objective": prob.value,
        "time_sec" : t1 - t0,
        "nodes"    : 0,
        "log_file" : f"data/results/{solver_name.lower()}_{model_stem}.log",
        "note"     : "LP relaxation (y_i ∈ [0,1])"
    }
    with open(RES_DIR / f"{solver_name.lower()}_{model_stem}.json", "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ {solver_name}: {model_stem} solved in {result['time_sec']:.2f}s – status {prob.status}")
    return result


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("lp_file")
    ap.add_argument("--time_limit", type=int, default=600)
    args = ap.parse_args()
    solve_lp(Path(args.lp_file), args.time_limit)
