"""
Solve a model with Google OR-Tools (CBC).
If only a .lp exists, convert it to .mps via HiGHS on-the-fly.

Produces:
    data/results/ortools-cbc_<model>.log
    data/results/ortools-cbc_<model>.json
"""

import os, json, time, contextlib
from pathlib import Path
from ortools.linear_solver import pywraplp

# ------------------------------------------------------------------
ROOT    = Path(os.environ["BENCHMARK_ROOT"]).resolve()
RES_DIR = ROOT / "data" / "results"
RES_DIR.mkdir(parents=True, exist_ok=True)
# ------------------------------------------------------------------


# ---------- LP ➜ MPS helper -----------------------------------------------
def _lp_to_mps(lp_path: Path) -> Path:
    """Return a .mps path, converting via HiGHS if needed."""
    mps_path = lp_path.with_suffix(".mps")
    if mps_path.exists():
        return mps_path

    try:
        import highspy
        h = highspy.Highs()
        h.readModel(str(lp_path))
        h.writeModel(str(mps_path))
        print(f"💾  Converted {lp_path.name} ➜ {mps_path.name} (HiGHS)")
    except Exception as e:
        raise RuntimeError(f"LP→MPS conversion failed: {e}")

    return mps_path
# ---------------------------------------------------------------------------


def solve_lp(lp_file: Path, time_limit: int = 600):
    model_name  = lp_file.stem
    solver_name = "ORtools-CBC"

    # 1️⃣  Ensure we have a .mps file
    mps_file = _lp_to_mps(lp_file)

    solver = pywraplp.Solver.CreateSolver("CBC")
    if solver is None:
        raise RuntimeError("CBC backend not available in this OR-Tools build.")

    # 2️⃣  Load the model (handle API differences)
    loaded = False
    for meth in ("ReadModelFromFile", "LoadModelFromFile", "ImportModelFromMps"):
        if hasattr(solver, meth):
            ret = getattr(solver, meth)(str(mps_file))
            if ret is None or ret == 0 or ret is True:
                loaded = True
            break

    solver.SetTimeLimit(time_limit * 1000)   # ms

    # 3️⃣  Solve with log capture
    log_path = RES_DIR / f"{solver_name.lower()}_{model_name}.log"
    with open(log_path, "w") as log_file, contextlib.redirect_stdout(log_file):
        t0 = time.perf_counter()
        status = solver.Solve()
        t1 = time.perf_counter()

    # 4️⃣  Collect metrics
    status_map = {
        pywraplp.Solver.OPTIMAL      : "OPTIMAL",
        pywraplp.Solver.FEASIBLE     : "FEASIBLE",
        pywraplp.Solver.INFEASIBLE   : "INFEASIBLE",
        pywraplp.Solver.UNBOUNDED    : "UNBOUNDED",
        pywraplp.Solver.ABNORMAL     : "ABNORMAL",
        pywraplp.Solver.NOT_SOLVED   : "NOT_SOLVED",
    }
    status_str = status_map.get(status, str(status))

    obj   = solver.Objective().Value() if status == pywraplp.Solver.OPTIMAL else float("nan")
    nodes = solver.nodes() if hasattr(solver, "nodes") else 0

    result = {
        "solver"   : solver_name,
        "model"    : model_name,
        "status"   : status_str,
        "objective": obj,
        "time_sec" : t1 - t0,
        "nodes"    : nodes,
        "log_file" : f"data/results/{solver_name.lower()}_{model_name}.log"
    }

    json_path = RES_DIR / f"{solver_name.lower()}_{model_name}.json"
    with open(json_path, "w") as f:
        json.dump(result, f, indent=2)

    print(f"✅ {solver_name}: {model_name} solved in {result['time_sec']:.2f}s – status {status_str}")
    return result


# ---------------- CLI helper ----------------------------------------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("lp_file", help="Path to .lp model")
    ap.add_argument("--time_limit", type=int, default=600)
    args = ap.parse_args()

    solve_lp(Path(args.lp_file), args.time_limit)
