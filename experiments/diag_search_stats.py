"""Glucose search statistics for commander vs product, over several clause orders.

For every board size and encoding it builds the CNF once, then solves it with Glucose4
several times: first with the original clause order (seed 0), then with shuffled orders
(seeds 1..K). It records PySAT's accumulated statistics (conflicts, decisions,
propagations). Solve-only time is measured around solver.solve_limited() and is NOT the
t_total of the main benchmark.

Usage (from the repo root, with the project interpreter):
  .venv/bin/python experiments/diag_search_stats.py --ns 32 64 100 200 --shuffles 5 \
      --out results/diag_search_stats.csv
"""
import argparse
import csv
import os
import random
import statistics
import sys
import time
from threading import Timer

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from pysat.solvers import Solver

from nqsat.amo import AMO_ENCODINGS
from nqsat.encode import build_cnf

FIELDS = ["n", "encoding", "seed", "status", "t_solve", "conflicts", "decisions", "propagations"]


def run(clauses, limit):
    s = Solver(name="glucose4", bootstrap_with=clauses)
    timer = Timer(limit, lambda: s.interrupt())
    timer.start()
    t0 = time.perf_counter()
    res = s.solve_limited(expect_interrupt=True)
    t = time.perf_counter() - t0
    timer.cancel()
    st = s.accum_stats()
    s.delete()
    status = "SAT" if res is True else ("UNSAT" if res is False else "TO")
    return status, t, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", type=int, nargs="+", default=[32, 64, 100, 200])
    ap.add_argument("--encs", nargs="+", default=["commander", "product"])
    ap.add_argument("--shuffles", type=int, default=5)
    ap.add_argument("--limit", type=int, default=120, help="seconds per solve")
    ap.add_argument("--out", default="results/diag_search_stats.csv")
    a = ap.parse_args()

    rows = []
    with open(a.out, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, lineterminator="\n")
        w.writeheader()
        for n in a.ns:
            for enc in a.encs:
                base, _ = build_cnf(n, AMO_ENCODINGS[enc])
                for seed in range(a.shuffles + 1):
                    cl = list(base)
                    if seed:
                        random.Random(seed).shuffle(cl)
                    status, t, st = run(cl, a.limit)
                    row = dict(n=n, encoding=enc, seed=seed, status=status, t_solve=round(t, 3),
                               conflicts=st.get("conflicts"), decisions=st.get("decisions"),
                               propagations=st.get("propagations"))
                    w.writerow(row); fh.flush(); rows.append(row)
                    print(f"N={n:4d} {enc:10s} seed={seed} {status:5s} t={t:8.3f}s "
                          f"conflicts={row['conflicts']} decisions={row['decisions']}", flush=True)

    print("\nMedian over clause orders (seed 0 = original order):")
    print(f"{'N':>5} {'enc':10s} {'runs':>4} {'t_solve':>9} {'conflicts':>11} {'decisions':>11} {'min..max conflicts':>22}")
    for n in a.ns:
        for enc in a.encs:
            g = [r for r in rows if r["n"] == n and r["encoding"] == enc and r["status"] != "TO"]
            if not g:
                print(f"{n:5d} {enc:10s}    0  (all timed out)"); continue
            cf = [r["conflicts"] for r in g]
            print(f"{n:5d} {enc:10s} {len(g):4d} {statistics.median(r['t_solve'] for r in g):9.3f} "
                  f"{statistics.median(cf):11.0f} {statistics.median(r['decisions'] for r in g):11.0f} "
                  f"{min(cf):>10d}..{max(cf):<10d}")


if __name__ == "__main__":
    main()
