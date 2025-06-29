# /plots/performance_profile.py
"""
Performance profile (Dolan–Moré) for solver runtimes.

Definition
----------
ρ_s(p) =  fraction of problems for which
          runtime_s,i  ≤  p ×  min_k(runtime_k,i)

Interpretation
--------------
• At p = 1   → “% of problems where the solver is the fastest.”
• As p grows → shows robustness; curves that rise steeply are better.

Usage
-----
    from benchmark.metrics import log_parser
    from benchmark.plots  import performance_profile

    summary = log_parser.load_summary()
    performance_profile.plot(summary, "perf_profile.png")
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


def _build_ratio_table(df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a wide table: rows=problem, cols=solver, values=time_ratio.
    """
    pivot = df.pivot(index="model", columns="solver", values="time_sec")
    best  = pivot.min(axis=1)
    ratio = pivot.div(best, axis=0)    # element-wise divide
    return ratio


def plot(summary_df: pd.DataFrame,
         out_file: str | Path = "performance_profile.png",
         title: str | None = None,
         p_max: float = 10.0,
         num_points: int = 200):
    """
    Parameters
    ----------
    summary_df : DataFrame
        Comes from metrics.log_parser.load_summary().
        Must have columns ['model','solver','time_sec'].
    out_file : str | Path
        PNG destination.
    p_max : float
        Horizontal axis upper bound (τ_max). 10 is typical.
    num_points : int
        Resolution of the curve.
    """
    ratio = _build_ratio_table(summary_df)

    tau_grid = np.linspace(1, p_max, num_points)
    plt.figure(figsize=(6, 4))

    for solver in ratio.columns:
        r = ratio[solver].dropna()
        if r.empty:
            continue
        prof = [(r <= t).mean() for t in tau_grid]
        plt.plot(tau_grid, prof, label=solver)

    plt.xscale("log")
    plt.xlim(1, p_max)
    plt.ylim(0, 1.05)
    plt.xlabel(r"Performance ratio  $\tau$")
    plt.ylabel("Fraction of problems solved")
    if title:
        plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"📉  performance-profile saved → {out_file}")
