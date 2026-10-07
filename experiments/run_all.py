import argparse
import csv
import json
import os
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

SAT_SOLVERS = ["cadical", "glucose", "cryptominisat", "kissat"]
ENCODINGS = ["pairwise", "seqcounter", "bitwise", "commander", "product"]
BASELINES = {
    "cpsat": ("nqsat.solvers_cpsat", "solve_cpsat"),
    "cpsat_bool": ("nqsat.solvers_cpsat_bool", "solve_cpsat_bool"),
    "gurobi": ("nqsat.solvers_gurobi", "solve_gurobi"),
    "cplex_mip": ("nqsat.solvers_cplex_mip", "solve_cplex_mip"),
    "cplex_cp": ("nqsat.solvers_cplex_cp", "solve_cplex_cp"),
}
COLS = ["solver", "encoding", "n", "rep", "sym", "status", "verify",
        "t_encode", "t_solve", "t_total", "nvars", "nclauses", "max_rss_mb"]
GRACE = 20  # seconds allowed on top of the limit for imports / process start-up


# ---------------------------------------------------------------- child
def child(solver, enc, n, timeout, sym):
    import importlib
    from nqsat.status import normalize
    from nqsat.verify import verify

    out = {"t_encode": "", "t_solve": "", "nvars": "", "nclauses": ""}
    if solver in SAT_SOLVERS:
        from nqsat.encode import build_cnf
        from nqsat.solvers_sat import AMO, solve_clauses
        t0 = time.perf_counter()
        clauses, top = build_cnf(n, AMO[enc], sym)
        t1 = time.perf_counter()
        out["nvars"], out["nclauses"] = top, len(clauses)
        status, queens = solve_clauses(n, clauses, solver)
        t2 = time.perf_counter()
        out["t_encode"], out["t_solve"], out["t_total"] = t1 - t0, t2 - t1, t2 - t0
    else:
        mod, fn = BASELINES[solver]
        f = getattr(importlib.import_module(mod), fn)
        t0 = time.perf_counter()
        status, queens = f(n, time_limit=timeout)
        out["t_total"] = time.perf_counter() - t0
    out["status"] = normalize(status)
    out["verify"] = verify(n, queens) if queens else ""
    print(json.dumps(out))


# --------------------------------------------------------------- parent
def group_rss_mb(pgid):
    """Total resident memory of every process in the run's process group."""
    total_kb = 0
    for pid in os.listdir("/proc"):
        if not pid.isdigit():
            continue
        try:
            with open(f"/proc/{pid}/status") as f:
                txt = f.read()
        except OSError:
            continue
        pg = rss = None
        for line in txt.splitlines():
            if line.startswith("NSpgid:"):
                pg = int(line.split()[1])
            elif line.startswith("VmRSS:"):
                rss = int(line.split()[1])
        if pg == pgid and rss:
            total_kb += rss
    return total_kb / 1024


def run_one(solver, enc, n, timeout, sym, mem_mb):
    cmd = [sys.executable, os.path.abspath(__file__), "--child",
           solver, enc, str(n), str(timeout), str(int(sym))]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                         text=True, start_new_session=True)
    start, peak, forced = time.time(), 0.0, None
    while p.poll() is None:
        time.sleep(0.05)
        peak = max(peak, group_rss_mb(p.pid))
        if peak > mem_mb:
            forced = "MO"
        elif time.time() - start > timeout + GRACE:
            forced = "TO"
        if forced:
            try:
                os.killpg(p.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            break
    out, _ = p.communicate()

    blank = {"verify": "", "t_encode": "", "t_solve": "", "t_total": "",
             "nvars": "", "nclauses": ""}
    if forced:
        res = dict(blank, status=forced)
        if forced == "TO":
            res["t_total"] = timeout
    else:
        try:
            res = json.loads(out.strip().splitlines()[-1])
        except Exception:
            res = dict(blank, status="MO" if p.returncode == -9 else "ERR")
        else:
            if res["status"] == "SAT" and res["verify"] is False:
                res["status"] = "ERR"          # wrong solution
            if res["status"] in ("SAT", "UNSAT") and res["t_total"] > timeout:
                res["status"] = "TO"           # finished, but over the limit
    res["max_rss_mb"] = round(peak)
    return res


def total_ram_mb():
    with open("/proc/meminfo") as f:
        return int(f.readline().split()[1]) / 1024


def fmt(x):
    return round(x, 3) if isinstance(x, float) else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ns", type=int, nargs="+",
                    default=[8, 16, 32, 64, 100, 150, 200, 300, 500, 1000])
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--sym", action="store_true", help="symmetry breaking (SAT solvers only)")
    ap.add_argument("--mem-frac", type=float, default=0.8)
    ap.add_argument("--only", nargs="+", default=None, help="restrict to these solvers")
    ap.add_argument("--out", default=os.path.join(HERE, "..", "results", "run_all.csv"))
    a = ap.parse_args()

    mem_mb = total_ram_mb() * a.mem_frac
    configs = [(s, e) for s in SAT_SOLVERS for e in ENCODINGS]
    configs += [(b, "-") for b in BASELINES]
    if a.only:
        configs = [c for c in configs if c[0] in a.only]

    done, dead = set(), {}
    if os.path.exists(a.out):
        with open(a.out) as f:
            for r in csv.DictReader(f):
                done.add((r["solver"], r["encoding"], int(r["n"]), int(r["rep"]), r["sym"]))
                if r["status"] in ("TO", "MO", "ERR"):
                    k = (r["solver"], r["encoding"])
                    dead[k] = min(dead.get(k, 10**9), int(r["n"]))

    new = not os.path.exists(a.out)
    print(f"timeout={a.timeout}s  mem limit={mem_mb:.0f} MB  reps={a.reps}  sym={a.sym}")
    with open(a.out, "a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS)
        if new:
            w.writeheader()

        def emit(s, e, n, rep, symstr, res):
            w.writerow({"solver": s, "encoding": e, "n": n, "rep": rep, "sym": symstr,
                        **{k: fmt(res.get(k, "")) for k in COLS[5:]}})
            fh.flush()

        for n in a.ns:
            for s, e in configs:
                symstr = str(int(a.sym and s in SAT_SOLVERS))
                d = dead.get((s, e))
                if d is not None and n > d:
                    if (s, e, n, 1, symstr) not in done:
                        emit(s, e, n, 1, symstr, {"status": "SKIP"})
                    continue
                for rep in range(1, a.reps + 1):
                    if (s, e, n, rep, symstr) in done:
                        continue
                    if d == n:
                        break
                    res = run_one(s, e, n, a.timeout, a.sym and s in SAT_SOLVERS, mem_mb)
                    emit(s, e, n, rep, symstr, res)
                    print(f"N={n:5d} {s:14s} {e:11s} rep{rep} {res['status']:4s} "
                          f"t={fmt(res.get('t_total', ''))} rss={res['max_rss_mb']}MB")
                    if res["status"] in ("TO", "MO", "ERR"):
                        dead[(s, e)] = min(dead.get((s, e), 10**9), n)
                        break


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--child":
        child(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]), bool(int(sys.argv[6])))
    else:
        main()
