import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKER = os.path.join(HERE, "..", "src", "nqsat", "worker.py")

SAT_SOLVERS = ["cadical", "glucose", "cryptominisat", "kissat"]
ENCODINGS = ["pairwise", "seqcounter", "bitwise", "commander", "product"]
BASELINES = ["cpsat", "cpsat_bool", "gurobi", "cplex_mip", "cplex_cp"]
FIELDS = ["n", "solver", "encoding", "rep", "nvars", "nclauses",
          "t_encode", "t_solve", "t_total", "status"]


def run_one(solver, enc, n, timeout, mem):
    cmd = [sys.executable, WORKER, solver, enc, str(n), str(timeout), str(mem)]
    grace = 0 if solver in SAT_SOLVERS else 20
    t0 = time.perf_counter()
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         text=True, start_new_session=True)
    try:
        out, err = p.communicate(timeout=timeout + grace)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        p.communicate()
        return {"status": "TO", "nvars": 0, "nclauses": 0, "t_encode": 0.0,
                "t_solve": 0.0, "t_total": time.perf_counter() - t0}
    wall = time.perf_counter() - t0
    res = None
    for line in out.splitlines():
        if line.startswith("RESULT:"):
            res = json.loads(line[7:])
    if res is None:
        res = {"status": "MO" if "MemoryError" in err else "ERR",
               "nvars": 0, "nclauses": 0, "t_encode": 0.0, "t_solve": 0.0}
    res["t_total"] = wall
    return res


def load_done(path):
    done, failed = set(), set()
    if os.path.exists(path):
        with open(path) as f:
            for r in csv.DictReader(f):
                done.add((int(r["n"]), r["solver"], r["encoding"], int(r["rep"])))
                if r["status"] in ("TO", "MO"):
                    failed.add((r["solver"], r["encoding"]))
    return done, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", type=int, nargs="+",
                    default=[8, 16, 32, 50, 100, 200, 300, 500, 1000])
    ap.add_argument("--reps", type=int, default=3)
    ap.add_argument("--timeout", type=float, default=300)
    ap.add_argument("--mem-gb", type=float, default=5)
    ap.add_argument("--out", default="results/results.csv")
    ap.add_argument("--solvers", nargs="+", default=SAT_SOLVERS + BASELINES)
    a = ap.parse_args()

    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    done, failed = load_done(a.out)
    new_file = not os.path.exists(a.out)
    f = open(a.out, "a", newline="")
    w = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
    if new_file:
        w.writeheader()

    configs = []
    for s in a.solvers:
        for e in (ENCODINGS if s in SAT_SOLVERS else ["-"]):
            configs.append((s, e))

    for n in sorted(a.ns):
        for s, e in configs:
            for rep in range(a.reps):
                if (n, s, e, rep) in done:
                    continue
                if (s, e) in failed:
                    row = {"status": "SKIP", "nvars": 0, "nclauses": 0,
                           "t_encode": 0, "t_solve": 0, "t_total": 0}
                else:
                    row = run_one(s, e, n, a.timeout, a.mem_gb)
                    if rep == 0 and row["status"] in ("TO", "MO"):
                        failed.add((s, e))
                row.pop("error", None)
                row.update(n=n, solver=s, encoding=e, rep=rep)
                w.writerow({k: (round(v, 4) if isinstance(v, float) else v)
                            for k, v in row.items() if k in FIELDS})
                f.flush()
                print(f"N={n:5d} {s:14s} {e:11s} rep={rep} "
                      f"{row['status']:5s} {row['t_total']:.2f}s", flush=True)


if __name__ == "__main__":
    main()
