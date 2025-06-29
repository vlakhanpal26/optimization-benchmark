"""
Random capacitated-facility-location (CFL) instance generator.

✅ What it does:
----------------
• Makes realistic test cases with user-chosen size (F facilities, C customers)
• Saves them both as:
      ├─ CSV files  → easy to open in Excel
      └─ .lp + .mps → for solvers like Gurobi / OR-Tools
• Keeps meta-info (size + seed) so results are reproducible.
"""

import os, json, argparse
from pathlib import Path
import numpy as np
import pandas as pd

# --- Paths
ROOT = Path(os.environ.get("BENCHMARK_ROOT", ".")).resolve()
INST_DIR = ROOT / "data" / "instances"
INST_DIR.mkdir(parents=True, exist_ok=True)


def generate_instance(F=50, C=100, seed=42):
    """Return a dict holding random data for a CFL problem."""
    rng = np.random.default_rng(seed)
    demand     = rng.integers(80, 200, size=C)
    capacity   = rng.integers(500, 1200, size=F)
    fixed_cost = rng.integers(5_000, 15_000, size=F)
    ship_cost  = rng.integers(10, 60, size=(F, C))

    return {
        "F": F, "C": C, "seed": seed,
        "demand": demand.tolist(),
        "capacity": capacity.tolist(),
        "fixed_cost": fixed_cost.tolist(),
        "ship_cost": ship_cost.tolist()
    }


# ---------- Save as .csv ---------------------------------------------------
def _save_csv(data, stem):
    p = INST_DIR / stem
    p.mkdir(parents=True, exist_ok=True)

    pd.Series(data["demand"]).to_csv(p / "demand.csv", index=False, header=False)
    pd.Series(data["capacity"]).to_csv(p / "capacity.csv", index=False, header=False)
    pd.Series(data["fixed_cost"]).to_csv(p / "fixed_cost.csv", index=False, header=False)
    pd.DataFrame(data["ship_cost"]).to_csv(p / "ship_cost.csv", index=False, header=False)

    with open(p / "meta.json", "w") as f:
        json.dump({k: data[k] for k in ("F", "C", "seed")}, f, indent=2)


# ---------- Write .lp model ------------------------------------------------
def _write_lp(data, stem):
    F, C = data["F"], data["C"]
    txt = ["Minimize"]

    for i in range(F):
        txt.append(f"  + {data['fixed_cost'][i]} y_{i}")
    for i in range(F):
        for j in range(C):
            txt.append(f"  + {data['ship_cost'][i][j]} x_{i}_{j}")

    txt.append("Subject To")
    for j in range(C):
        lhs = " + ".join(f"x_{i}_{j}" for i in range(F))
        txt.append(f"  dem_{j}: {lhs} = {data['demand'][j]}")
    for i in range(F):
        lhs = " + ".join(f"x_{i}_{j}" for j in range(C))
        txt.append(f"  cap_{i}: {lhs} - {data['capacity'][i]} y_{i} <= 0")

    txt.append("Bounds")
    for i in range(F):
        for j in range(C):
            txt.append(f"  x_{i}_{j} >= 0")

    txt.append("Binary")
    for i in range(F):
        txt.append(f"  y_{i}")

    txt.append("End")
    (INST_DIR / f"{stem}.lp").write_text("\n".join(txt))


# ---------- Write .mps model using PuLP ------------------------------------
def _write_mps(data, stem):
    from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary

    F, C = data["F"], data["C"]
    prob = LpProblem(name=stem, sense=LpMinimize)

    x = {(i, j): LpVariable(f"x_{i}_{j}", lowBound=0) for i in range(F) for j in range(C)}
    y = {i: LpVariable(f"y_{i}", cat=LpBinary) for i in range(F)}

    prob += lpSum(data["fixed_cost"][i] * y[i] for i in range(F)) + \
            lpSum(data["ship_cost"][i][j] * x[i, j] for i in range(F) for j in range(C))

    for j in range(C):
        prob += lpSum(x[i, j] for i in range(F)) == data["demand"][j], f"demand_{j}"
    for i in range(F):
        prob += lpSum(x[i, j] for j in range(C)) <= data["capacity"][i] * y[i], f"capacity_{i}"

    mps_path = INST_DIR / f"{stem}.mps"
    print(f"📝 Writing MPS to {mps_path}")
    prob.writeMPS(str(mps_path))

    if mps_path.exists():
        print(f"✅ MPS file written: {mps_path}")
    else:
        print(f"❌ Failed to write MPS: {mps_path}")


# ---------- Top-level helper -----------------------------------------------
def build_and_save(F=150, C=300, seed=42):
    """Generate and save CFL instance as .csv + .lp + .mps."""
    data = generate_instance(F, C, seed)
    stem = f"cfl_F{F}_C{C}_seed{seed}"
    _save_csv(data, stem)
    _write_lp(data, stem)
    _write_mps(data, stem)
    print(f"\n📦 Instance saved: {stem} (.csv, .lp, .mps)")


# ---------- CLI interface --------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--facilities", type=int, default=150)
    ap.add_argument("--customers",  type=int, default=300)
    ap.add_argument("--seed",       type=int, default=42)
    args = ap.parse_args()

    build_and_save(args.facilities, args.customers, args.seed)
