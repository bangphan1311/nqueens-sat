"""Diagnostic Glucose4 search statistics for Commander vs Product.

Run from the project root with:
  uv run --no-project --with python-sat python experiments/glucose_stats.py

Writes only results/exploratory/glucose_stats.csv and refuses to overwrite it.
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
DEFAULT_OUT = Path("results/exploratory/glucose_stats.csv")
FIELDS = (
    "n", "solver", "encoding", "rep", "nvars", "nclauses",
    "t_encode", "t_solve", "t_total", "status", "verify",
    "conflicts", "decisions", "propagations", "restarts", "error",
)
ENCODINGS = ("commander", "product")


def worker(n: int, encoding: str) -> int:
    """Run one instance and print its result as a JSON line."""
    sys.path.insert(0, str(SRC))
    result = {
        "nvars": 0, "nclauses": 0, "t_encode": 0.0, "t_solve": 0.0,
        "status": "ERR", "verify": "", "conflicts": "", "decisions": "",
        "propagations": "", "restarts": "", "error": "",
    }
    try:
        from pysat.solvers import Solver
        from nqsat import amo
        from nqsat.encode import build_cnf, decode
        from nqsat.verify import verify

        encoders = {
            "commander": amo.amo_commander,
            "product": amo.amo_product,
        }
        t0 = time.perf_counter()
        clauses, top = build_cnf(n, encoders[encoding], sym=False)
        result["t_encode"] = time.perf_counter() - t0
        result["nvars"] = top
        result["nclauses"] = len(clauses)

        t1 = time.perf_counter()
        with Solver(name="glucose4", bootstrap_with=clauses) as solver:
            sat = solver.solve()
            stats = solver.accum_stats()
            model = solver.get_model() if sat else None
        result["t_solve"] = time.perf_counter() - t1

        for key in ("conflicts", "decisions", "propagations", "restarts"):
            result[key] = stats.get(key, "")

        if sat and model is not None:
            is_valid = bool(verify(n, decode(n, model)))
            result["verify"] = is_valid
            result["status"] = "SAT" if is_valid else "ERR"
            if not is_valid:
                result["error"] = "SAT model failed the independent verifier"
        else:
            result["status"] = "UNSAT"
    except Exception as exc:
        result["status"] = "ERR"
        result["error"] = repr(exc)[:400]

    print("RESULT:" + json.dumps(result), flush=True)
    return 0


def run_case(n: int, encoding: str, timeout: float) -> dict:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(n), encoding]
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            cmd, cwd=ROOT, capture_output=True, text=True,
            timeout=timeout, encoding="utf-8", errors="replace",
        )
        total = time.perf_counter() - started
        payload = next(
            (line[len("RESULT:"):] for line in completed.stdout.splitlines()
             if line.startswith("RESULT:")),
            None,
        )
        if payload is None:
            return {
                "nvars": 0, "nclauses": 0, "t_encode": 0.0, "t_solve": 0.0,
                "t_total": total, "status": "ERR", "verify": "",
                "conflicts": "", "decisions": "", "propagations": "",
                "restarts": "", "error": (completed.stderr or completed.stdout or
                    f"Worker exited with code {completed.returncode}")[-500:],
            }
        result = json.loads(payload)
        result["t_total"] = total
        return result
    except subprocess.TimeoutExpired:
        return {
            "nvars": 0, "nclauses": 0, "t_encode": 0.0, "t_solve": 0.0,
            "t_total": time.perf_counter() - started, "status": "TO", "verify": "",
            "conflicts": "", "decisions": "", "propagations": "", "restarts": "",
            "error": f"Parent timeout after {timeout:g}s",
        }


def main() -> int:
    parser = argparse.ArgumentParser(description="Glucose4 search-statistics diagnostic")
    parser.add_argument("--ns", nargs="+", type=int, default=[32, 64])
    parser.add_argument("--encodings", nargs="+", choices=ENCODINGS, default=list(ENCODINGS))
    parser.add_argument("--reps", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=90.0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    if args.reps < 1 or args.timeout <= 0:
        parser.error("--reps must be >= 1 and --timeout must be > 0")
    if any(n < 4 for n in args.ns):
        parser.error("N must be >= 4 for these satisfiable N-Queens instances")

    output = args.out if args.out.is_absolute() else ROOT / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        parser.error(f"Output already exists; refusing to overwrite: {output}")

    print(f"Solver: Glucose4 | N={args.ns} | encodings={args.encodings}", flush=True)
    print(f"Repetitions/configuration: {args.reps} | timeout/run: {args.timeout:g}s", flush=True)
    print(f"Output: {output}", flush=True)

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        handle.flush()
        for n in args.ns:
            for encoding in args.encodings:
                for rep in range(1, args.reps + 1):
                    print(f"Running N={n}, encoding={encoding}, rep={rep}/{args.reps} ...", flush=True)
                    result = run_case(n, encoding, args.timeout)
                    row = {
                        "n": n, "solver": "glucose4", "encoding": encoding,
                        "rep": rep, **result,
                    }
                    writer.writerow(row)
                    handle.flush()
                    print(
                        f"  status={row['status']} verify={row['verify']} "
                        f"t_solve={float(row['t_solve'] or 0):.3f}s "
                        f"conflicts={row['conflicts']} decisions={row['decisions']} "
                        f"propagations={row['propagations']}", flush=True,
                    )

    print(f"Finished. Results saved to {output}", flush=True)
    return 0


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "--worker":
        if len(sys.argv) != 4:
            raise SystemExit("Usage: glucose_stats.py --worker N commander|product")
        raise SystemExit(worker(int(sys.argv[2]), sys.argv[3]))
    raise SystemExit(main())
