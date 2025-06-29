# Optimization-solver benchmark

Hi I’m **Vedika**, an IE grad student. With this project, I wanted to chekc different solvers and their speeds on a **classic MIP**: the _Capacitated Facility-Location_ problem (CFL).

This repo contains:

* **Three automatically-sized CFL instances**  
  &nbsp;&nbsp;_small (50 × 100) • medium (100 × 200) • large (150 × 300)_
* **Four solvers** tested out-of-the-box  
  * HiGHS (open) * OR-Tools CBC (open)  
  * Clarabel (open, convex—used on the LP relaxation)  
  * Gurobi (academic license)
* A **one-click pipeline** that generates data, runs every solver, parses the logs, and spits out PNG plots for a blog post / report.

---

## TL;DR results (Colab single core, 600 s limit)

| instance | HiGHS (MIP) | OR-Tools CBC | Gurobi (MIP) | Clarabel (LP) |
|----------|-------------|--------------|--------------|---------------|
| small    | 7.8 s | <0.1 s | **0.97 s** | 0.11 s |
| medium   | 29 s | <0.1 s | **6.1 s** | 0.62 s |
| large    | **44 s** | <0.1 s | 3.5 s | 1.3 s |

<details>
<summary>What i observed?</summary>

* CBC is _fast_ on these particular instances once converted to MPS.
* Clarabel’s LP relaxation is orders of magnitude faster, but obviously ignores integrality.
* Gurobi dominates on “medium”, HiGHS wins on “large” within the 600 s wallclock.
</details>

---

## Quick start (Colab or local)

```bash
# 1. clone & install deps
git clone https://github.com/vlakhanpal26/optimization-benchmark.git
cd optimization-benchmark
pip install -r requirements.txt  # adds highspy, ortools, cvxpy, clarabel

# 2. (optional) activate a Gurobi academic/WLS license
export GRB_WLSACCESSID=... GRB_WLSSECRET=... GRB_LICENSEID=...

# 3. generate LP + CSV data
python main.py gen --sizes all          # small / medium / large

# 4. run every solver (10 min total on Colab free tier)
python main.py run-all --time 600

# 5. make plots & table for the blog / paper
python main.py plots
open plots/perf_profile.png


