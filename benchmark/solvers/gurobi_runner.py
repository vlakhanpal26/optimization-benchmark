# /solvers/gurobi_runner.py
"""
Solve a .lp file with Gurobi, save log & JSON metrics.

Interface:
    from solvers.gurobi_runner import solve_lp
    solve_lp(Path('data/instances/... .lp'), time_limit=600)
"""

import os, json, time
from pathlib import Path

os.environ['GRB_WLSACCESSID'] = '6ee2bf52-8ba7-4500-b215-10a9376ef46d'
os.environ['GRB_WLSSECRET']   = '4a5f87d9-b196-46a9-9eb5-139bed9a3f87'
os.environ['GRB_LICENSEID']   = '2680325'

import gurobipy as gp

ROOT    = Path(os.environ["BENCHMARK_ROOT"]).resolve()
RES_DIR = ROOT / "data" / "results"
RES_DIR.mkdir(parents=True, exist_ok=True)


def solve_lp(lp_file: Path, time_limit: int = 600):
    model_name  = lp_file.stem
    solver_name = "Gurobi"

    # 1️⃣  Read model ---------------------------------------------------------
    # Create Gurobi environment explicitly using WLS credentials
    # Create cloud environment with WLS credentials
    env = gp.Env(empty=True)
    env.setParam('WLSAccessID', os.environ['GRB_WLSACCESSID'])
    env.setParam('WLSSecret',   os.environ['GRB_WLSSECRET'])
    env.setParam('LicenseID',   int(os.environ['GRB_LICENSEID']))
    env.start()

    m = gp.read(str(lp_file), env)


    # 2️⃣  Options ------------------------------------------------------------
    m.Params.TimeLimit   = time_limit       # seconds
    m.Params.OutputFlag  = 1                # print on screen
    m.Params.LogFile     = str(RES_DIR / f"{solver_name.lower()}_{model_name}.log")
    # (optional) cut/pass/integrality params can be tuned here

    # 3️⃣  Solve --------------------------------------------------------------
    t0 = time.perf_counter()
    m.optimize()
    t1 = time.perf_counter()

    # 4️⃣  Collect basic info -------------------------------------------------
    status = m.Status                      # numeric code
    status_codes = {v: k for k, v in gp.GRB.Status.__dict__.items() if isinstance(v, int)}
    status_str = status_codes.get(status, str(status))

    obj    = m.ObjVal if m.Status == gp.GRB.OPTIMAL else float("nan")
    nodes  = int(m.NodeCount)

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


# --- CLI helper -------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("lp_file")
    ap.add_argument("--time_limit", type=int, default=600)
    args = ap.parse_args()

    solve_lp(Path(args.lp_file), args.time_limit)

