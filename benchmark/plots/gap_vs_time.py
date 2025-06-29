# /plots/gap_vs_time.py
"""
Create a gap-vs-time line chart for every solver that has
progress data (built by metrics.log_parser.load_progress).

Rules (per project conventions)
--------------------------------
• matplotlib only (no seaborn)
• exactly ONE figure – no subplots
• use default color cycle (don’t set colors manually)
"""

import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import os


def plot(progress_df: pd.DataFrame,
         out_file: str | Path = "gap_vs_time.png",
         title: str | None = None):
    """
    Parameters
    ----------
    progress_df : DataFrame
        Columns = ['solver','model','time_sec','gap_pct']
    out_file : str | Path
        Destination image path (PNG).
    title : str | None
        Optional chart title.
    """
    if progress_df.empty:
        raise ValueError("progress_df has no rows – nothing to plot.")

    # --------- ONE figure -------------
    plt.figure(figsize=(6, 4))  # default color cycle

    for solver, grp in progress_df.groupby("solver"):
        # Use the *last* recorded gap for each time point of that solver.
        grp_sorted = grp.sort_values("time_sec")
        plt.plot(grp_sorted["time_sec"],
                 grp_sorted["gap_pct"],
                 label=solver)

    plt.yscale("log")
    plt.xlabel("Time (seconds)")
    plt.ylabel("Gap to best (%)")
    if title:
        plt.title(title)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_file, dpi=300)
    plt.close()
    print(f"📈  gap-vs-time chart saved → {out_file}")
