# /metrics/log_parser.py
"""
Helpers to transform solver outputs → pandas DataFrames
so downstream plotting functions stay one-liners.

Public API
----------
load_summary(results_dir=...)        → DF with one row per solver × model
load_progress(results_dir=...)       → DF with gap-vs-time lines
"""

import json, re
from pathlib import Path
from typing import List
import pandas as pd

# ------------------------------------------------------------------
from pathlib import Path
import os
ROOT     = Path(os.environ["BENCHMARK_ROOT"]).resolve()
RES_DIR  = ROOT / "data" / "results"
# ------------------------------------------------------------------


# ------------------------------------------------------------------
# 1️⃣  FINAL SUMMARY TABLE  (just read the small JSON files)
# ------------------------------------------------------------------
def load_summary(results_dir: Path = RES_DIR) -> pd.DataFrame:
    """Return dataframe with one row per *.json result file."""
    rows = []
    for jf in results_dir.glob("*.json"):
        with open(jf) as f:
            d = json.load(f)
        rows.append(d)
    if not rows:
        raise FileNotFoundError(f"No JSON files found in {results_dir}")
    return pd.DataFrame(rows)


# ------------------------------------------------------------------
# 2️⃣  GAP-vs-TIME CURVES  (parse each solver’s log)
# ------------------------------------------------------------------

def _parse_gurobi_log(path: Path, model: str, solver: str) -> List[dict]:
    """
    Extract (time_sec, gap_pct) from Gurobi progress lines like:

      0    0     0.00s          0          -          -        -      - 
     10   10     0.24s     1.32e+03   3.12e+03   5.76e+02  132%   0.24s
    """
    patt = re.compile(r"^\s*\d+\s+\d+\s+(\d+\.\d+)s\s+[-\d.e+]+\s+[-\d.e+]+\s+[-\d.e+]+\s+([\d\.]+)%")
    rows = []
    for line in path.read_text().splitlines():
        m = patt.match(line)
        if m:
            t, gap = map(float, m.groups())
            rows.append({"time_sec": t, "gap_pct": gap, "model": model, "solver": solver})
    return rows


def _parse_highs_log(path: Path, model: str, solver: str) -> List[dict]:
    """
    HiGHS prints lines like:
      13s: status =  7; MIP gap = 45.67%; ...
    """
    patt = re.compile(r"^\s*(\d+)s: .*MIP gap =\s*([\d\.]+)%")
    rows = []
    for line in path.read_text().splitlines():
        m = patt.match(line)
        if m:
            t, gap = m.groups()
            rows.append({"time_sec": float(t), "gap_pct": float(gap),
                         "model": model, "solver": solver})
    return rows


_PARSERS = {
    "gurobi": _parse_gurobi_log,
    "highs":  _parse_highs_log,
    # OR-Tools & Clarabel do not report a running gap by default; feel free to add.
}


def load_progress(results_dir: Path = RES_DIR) -> pd.DataFrame:
    """
    Returns DF with columns [solver, model, time_sec, gap_pct]
    combining every log parser that yields non-empty data.
    """
    all_rows = []
    for log in results_dir.glob("*.log"):
        solver_key = log.stem.split("_")[0]       # e.g., 'gurobi'
        model      = "_".join(log.stem.split("_")[1:])
        parser     = _PARSERS.get(solver_key.lower())
        if parser:
            rows = parser(log, model, solver_key.capitalize())
            all_rows.extend(rows)

    if not all_rows:
        raise RuntimeError("No progress data parsed; check log patterns.")
    return pd.DataFrame(all_rows)
