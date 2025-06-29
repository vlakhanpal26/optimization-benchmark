"""
Main CLI for the optimisation-solver benchmark.

Typical usage
-------------
# 1. Solve three instance sizes with all solvers & make plots
python main.py run-all

# 2. Just regenerate instances
python main.py gen --sizes small medium

# 3. Solve one LP with HiGHS only
python main.py solve \
        --lp data/instances/cfl_F150_C300_seed42.lp \
        --solvers highs
"""

from pathlib import Path
import importlib
import argparse, sys, os, itertools
os.environ['GRB_WLSACCESSID'] = '6ee2bf52-8ba7-4500-b215-10a9376ef46d'
os.environ['GRB_WLSSECRET']   = '4a5f87d9-b196-46a9-9eb5-139bed9a3f87'
os.environ['GRB_LICENSEID']   = '2680325'

# ------------------------------------------------------------------
ROOT = Path(os.environ["BENCHMARK_ROOT"]).resolve()
INST_DIR = ROOT / "data" / "instances"
RES_DIR  = ROOT / "data" / "results"
PLOTS_DIR = ROOT / "plots"
for p in (INST_DIR, RES_DIR, PLOTS_DIR):
    p.mkdir(parents=True, exist_ok=True)
# ------------------------------------------------------------------

# -------------------------------------------------------------
# 1️⃣  instance sizes you want in the blog
SIZES = {
    "small":  (50, 100),
    "medium": (100, 200),
    "large":  (150, 300)
}
SEED = 42
# -------------------------------------------------------------

# -------------------------------------------------------------
# helper to import runner dynamically
RUNNERS = {
    "highs"   : "benchmark.solvers.highs_runner",
    "gurobi"  : "benchmark.solvers.gurobi_runner",
    "ortools" : "benchmark.solvers.ortools_runner",
    "clarabel": "benchmark.solvers.clarabel_runner"
}
# -------------------------------------------------------------

def ensure_instance(size_key: str):
    """Generate data if it doesn't exist yet."""
    F, C = SIZES[size_key]
    stem = f"cfl_F{F}_C{C}_seed{SEED}"
    lp_path = INST_DIR / f"{stem}.lp"
    if lp_path.exists():
        return lp_path
    print(f"🛠️  generating instance {stem}")
    from benchmark.problems.facility_location import build_and_save
    build_and_save(F, C, SEED)
    return lp_path


def solve_one(lp_path: Path, solver_key: str, time_limit: int):
    mod = importlib.import_module(RUNNERS[solver_key])
    return mod.solve_lp(lp_path, time_limit=time_limit)


def run_all(time_limit: int):
    # 1. make sure all instances are on disk
    paths = {k: ensure_instance(k) for k in SIZES}

    # 2. run every solver × every instance
    for size_key, lp in paths.items():
        for solver_key in RUNNERS:
            print(f"\n=== {solver_key.upper()}  |  {size_key} ===")
            solve_one(lp, solver_key, time_limit)

    # 3. build plots
    from benchmark.metrics import log_parser
    from benchmark.plots  import gap_vs_time, performance_profile, scalability_curve

    summary = log_parser.load_summary()
    try:
        prog = log_parser.load_progress()
        gap_vs_time.plot(prog, PLOTS_DIR / "gap_curve.png",
                         title="Gap vs time")
    except Exception as e:
        print("Gap-curve skipped:", e)

    performance_profile.plot(summary, PLOTS_DIR / "perf_profile.png",
                             title="Performance profile")
    scalability_curve.plot(summary, PLOTS_DIR / "scale.png",
                           title="Scalability curve")

    print("\n✅  All done – plots saved under /plots")


# -------------------------------------------------------------
# CLI
# -------------------------------------------------------------
if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    p_all = sub.add_parser("run-all")
    p_all.add_argument("--time", type=int, default=600,
                       help="time-limit per solver (s)")

    p_gen = sub.add_parser("gen")
    p_gen.add_argument("--sizes", nargs="+",
                       choices=SIZES.keys(), default=list(SIZES),
                       help="which instance sizes to generate")

    p_solve = sub.add_parser("solve")
    p_solve.add_argument("--lp", required=True,
                         help="path to .lp model")
    p_solve.add_argument("--solvers", nargs="+",
                         choices=RUNNERS.keys(), default=list(RUNNERS))
    p_solve.add_argument("--time", type=int, default=600)

    args = ap.parse_args()

    if args.cmd == "run-all":
        run_all(args.time)

    elif args.cmd == "gen":
        for sz in args.sizes:
            ensure_instance(sz)

    elif args.cmd == "solve":
        lp = Path(args.lp)
        for s in args.solvers:
            solve_one(lp, s, args.time)

