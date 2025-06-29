# /plots/scalability_curve.py
"""
Scalability curve:  solve-time  vs  number-of-variables.

Assumptions
-----------
• Model names follow  'cfl_F{fac}_C{cust}_seed{...}'
  (as produced by problems.facility_location).  
• Number of vars  =  F * C (x_ij)  +  F (y_i).

Usage
-----
    from benchmark.metrics import log_parser
    from benchmark.plots  import scalability_curve

    summary = log_parser.load_summary()
    scalability_curve.plot(summary,
                           out_file="scale.png",
                           title="CFL scalability")
"""

import re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt


def _derive_vars(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'num_vars' column parsed from model string if absent.
    """
    if "num_vars" in df.columns:
        return df
    pat = re.compile(r"F(\d+)_C(\d+)_")
    nums = []
    for m in df["model"]:
        m = str(m)
        mo = pat.search(m)
        if mo:
            F, C = map(int, mo.groups())
            nums.append(F * C + F)          # x_ij plus y_i
        else:
            nums.append(float("nan"))
    df = df.copy()
    df["num_vars"] = nums
    return df


def plot(summary_df: pd.DataFrame,
         out_file: str | Path = "scalability_curve.png",
         title: str | None = None):
    """
    Parameters
    ----------
    summary_df : DataFrame
        Columns must include ['solver','model','time_sec'].
        'num_vars' added automatically if pattern matches.
    out_file : str | Path
        Destination PNG.
    """
    df = _derive_vars(summary_df)
    if df["num_vars"].isna().any():
        raise ValueError("Some rows missing num_vars – check model names.")

    plt.figure(figsize=(6, 4))   # single figure

    for solver, grp in df.groupby("solver"):
        grp_sorted = grp.sort_values("num_vars")
        plt.plot(grp_sorted["num_vars"],
                 grp_sorted["time_sec"],
                 marker="o",
                 label=solver)

    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Number of variables  (log)")
    plt.ylabel("Solve time (seconds, log)")
    if title:
        plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"📊  scalability curve saved → {out_file}")
