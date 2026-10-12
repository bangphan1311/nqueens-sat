import csv
import subprocess
import sys
import tempfile
from pathlib import Path

from run_all import load_done, should_skip

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "experiments" / "run_all.py"
FIELDS = [
    "n", "solver", "encoding", "sym", "rep", "nvars", "nclauses",
    "t_encode", "t_solve", "t_total", "status",
]


def make_row(n, sym, rep, status):
    return {
        "n": n,
        "solver": "cadical",
        "encoding": "commander",
        "sym": sym,
        "rep": rep,
        "nvars": 0,
        "nclauses": 0,
        "t_encode": 0,
        "t_solve": 0,
        "t_total": 30 if status == "TO" else 0,
        "status": status,
    }


def read_rows(path):
    with path.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_runner(path, ns, reps=1, sym=False):
    cmd = [
        sys.executable, str(RUNNER),
        "--ns", *[str(n) for n in ns],
        "--reps", str(reps),
        "--timeout", "30",
        "--mem-gb", "5",
        "--solvers", "cadical",
        "--encs", "commander",
        "--out", str(path),
    ]
    if sym:
        cmd.append("--sym")

    result = subprocess.run(
        cmd, cwd=ROOT, capture_output=True, text=True, timeout=90
    )
    print(result.stdout, end="")
    if result.returncode != 0:
        raise AssertionError(
            f"Runner exited {result.returncode}\nSTDERR:\n{result.stderr}"
        )


def main():
    with tempfile.TemporaryDirectory(prefix="nqsat_resume_test_") as tmp:
        path = Path(tmp) / "partial.csv"

        # Simulate a previous interrupted run: timeout at N=300.
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS, lineterminator="\n")
            writer.writeheader()
            writer.writerow(make_row(300, 0, 0, "TO"))
            writer.writerow(make_row(300, 0, 1, "SKIP"))

        done, failed = load_done(path)

        assert (300, "cadical", "commander", 0, 0) in done
        assert failed[("cadical", "commander", 0)] == 300
        assert not should_skip(100, "cadical", "commander", 0, failed)
        assert should_skip(300, "cadical", "commander", 0, failed)
        assert not should_skip(300, "cadical", "commander", 1, failed)
        print("PASS: unit checks for cutoff and symmetry separation.")

        # A missing smaller N must still run despite the N=300 timeout.
        run_runner(path, [100])
        rows = read_rows(path)
        assert any(
            r["n"] == "100" and r["sym"] == "0"
            and r["rep"] == "0" and r["status"] == "SAT"
            for r in rows
        ), "Missing smaller N did not run successfully"
        print("PASS: resume executes a missing smaller instance.")

        # Existing rep=0 and rep=1 remain untouched; missing rep=2 is skipped.
        run_runner(path, [300], reps=3)
        rows = read_rows(path)
        assert any(
            r["n"] == "300" and r["sym"] == "0"
            and r["rep"] == "2" and r["status"] == "SKIP"
            for r in rows
        ), "Expected rep=2 at the failed cutoff to be SKIP"
        print("PASS: missing repetitions at the cutoff are recorded as SKIP.")

        # The same N and encoding under symmetry breaking is independent.
        run_runner(path, [300], sym=True)
        rows = read_rows(path)
        assert any(
            r["n"] == "300" and r["sym"] == "1"
            and r["rep"] == "0" and r["status"] == "SAT"
            for r in rows
        ), "Symmetry-enabled run was incorrectly skipped or did not solve"
        print("PASS: symmetry-enabled run executes independently.")

    print("ALL RESUME INTEGRATION TESTS PASSED.")


if __name__ == "__main__":
    main()
