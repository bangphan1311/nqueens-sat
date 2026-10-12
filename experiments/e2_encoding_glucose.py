"""E2: compare all five N-Queens AMO encodings using Glucose4.

Run from the project root with:
  uv run --no-project --with python-sat python experiments/e2_encoding_glucose.py

The parent runs each case in a child process so a timeout can be enforced on Windows.
Raw output is written to results/e2_encoding_glucose.csv. Existing output is never overwritten.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
OUTPUT = ROOT / "results" / "e2_encoding_glucose.csv"
ENCODINGS = ("pairwise", "seqcounter", "bitwise", "commander", "product")
DEFAULT_NS = (16, 32, 50, 64)
FIELDS = (
    "n", "solver", "encoding", "rep", "nvars", "nclauses",
    "t_encode", "t_solve", "t_total", "status", "verify", "error",
)


def worker(n: int, encoding: str) -> int:
    """Execute one measured case and emit exactly one RESULT JSON line."""
    import os

    sys.path.insert(0, str(SRC))
    result = {
        "nvars": 0,
        "nclauses": 0,
        "t_encode": 0.0,
        "t_solve": 0.0,
        "status": "ERR",
        "verify": "",
        "error": "",
    }
    try:
        from pysat.solvers import Solver
        from nqsat import amo
        from nqsat.encode import build_cnf, decode
        from nqsat.verify import verify

        encoder_map = {
            "pairwise": amo.amo_pairwise,
            "seqcounter": amo.amo_seqcounter,
            "bitwise": amo.amo_bitwise,
            "commander": amo.amo_commander,
            "product": amo.amo_product,
        }
        t0 = time.perf_counter()
        clauses, top = build_cnf(n, encoder_map[encoding], sym=False)
        result["t_encode"] = time.perf_counter() - t0
        result["nvars"] = top
        result["nclauses"] = len(clauses)

        t1 = time.perf_counter()
        with Solver(name="glucose4", bootstrap_with=clauses) as solver:
            sat = solver.solve()
            model = solver.get_model() if sat else None
        if sat:
            queens = decode(n, model)
            valid = bool(verify(n, queens))
            result["verify"] = valid
            result["status"] = "SAT" if valid else "ERR"
            if not valid:
                result["error"] = "Solver returned SAT but verifier rejected the decoded solution"
        else:
            result["status"] = "UNSAT"
        result["t_solve"] = time.perf_counter() - t1
    except MemoryError:
        result["status"] = "MO"
        result["error"] = "MemoryError"
    except Exception as exc:  # Keep the failure in the raw results rather than lose it.
        result["status"] = "ERR"
        result["error"] = repr(exc)[:300]

    print("RESULT:" + json.dumps(result), flush=True)
    return 0


def run_case(n: int, encoding: str, timeout: float) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(n), encoding]
    start = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
        total = time.perf_counter() - start
        payload = None
        for line in completed.stdout.splitlines():
            if line.startswith("RESULT:"):
                payload = line[len("RESULT:"):]
        if payload is None:
            return {
                "nvars": 0, "nclauses": 0, "t_encode": 0.0,
                "t_solve": 0.0, "t_total": total, "status": "ERR",
                "verify": "", "error": (completed.stderr or completed.stdout or
                                           f"worker exited with code {completed.returncode}")[-500:],
            }
        result = json.loads(payload)
        result["t_total"] = total
        return result
    except subprocess.TimeoutExpired:
        return {
            "nvars": 0, "nclauses": 0, "t_encode": 0.0,
            "t_solve": 0.0, "t_total": time.perf_counter() - start,
            "status": "TO", "verify": "", "error": f"Timeout after {timeout:g}s",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="E2: Glucose4 encoding comparison")
    parser.add_argument("--ns", nargs="+", type=int, default=list(DEFAULT_NS))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument("--out", type=Path, default=OUTPUT)
    args = parser.parse_args()

    if args.reps < 1 or args.timeout <= 0:
        parser.error("--reps must be >= 1 and --timeout must be > 0")
    if any(n < 4 for n in args.ns):
        parser.error("N-Queens E2 requires N >= 4 for these satisfiable instances")

    out = args.out if args.out.is_absolute() else ROOT / args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        parser.error(f"Output already exists; refusing to overwrite raw data: {out}")

    print("E2 configuration:", flush=True)
    print(f"  solver=glucose4; N={args.ns}; encodings={list(ENCODINGS)}", flush=True)
    print(f"  repetitions={args.reps}; timeout/run={args.timeout:g}s", flush=True)
    print(f"  output={out}", flush=True)
    print("  t_total is parent wall time (includes worker-process startup); SAT is retained only if verify=True.", flush=True)

    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        handle.flush()
        for n in args.ns:
            for encoding in ENCODINGS:
                config_failed = False
                for rep in range(args.reps):
                    if config_failed:
                        result = {
                            "nvars": 0, "nclauses": 0, "t_encode": 0.0,
                            "t_solve": 0.0, "t_total": 0.0,
                            "status": "SKIP", "verify": "", "error": "Prior repetition was not SAT",
                        }
                    else:
                        print(f"Running N={n}, encoding={encoding}, rep={rep} ...", flush=True)
                        result = run_case(n, encoding, args.timeout)
                        if result["status"] != "SAT" or result.get("verify") is not True:
                            config_failed = True
                    row = {
                        "n": n, "solver": "glucose4", "encoding": encoding, "rep": rep,
                        **result,
                    }
                    writer.writerow(row)
                    handle.flush()
                    print(
                        f"  status={row['status']} verify={row['verify']} "
                        f"total={float(row['t_total']):.3f}s "
                        f"vars={row['nvars']} clauses={row['nclauses']}",
                        flush=True,
                    )

    print(f"E2 complete. Results saved to: {out}", flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--worker":
        if len(sys.argv) != 4:
            print("Worker usage: --worker N encoding", file=sys.stderr)
            raise SystemExit(2)
        raise SystemExit(worker(int(sys.argv[2]), sys.argv[3]))
    raise SystemExit(main())
