import os
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nqsat import amo as A
from nqsat.encode import build_cnf, decode

KISSAT = os.path.expanduser("~/kissat/build/kissat")

AMO = {
    "pairwise": A.amo_pairwise,
    "seqcounter": A.amo_seqcounter,
    "bitwise": A.amo_bitwise,
    "commander": A.amo_commander,
    "product": A.amo_product,
}

PYSAT_NAMES = {"cadical": "cadical153", "glucose": "glucose4"}


def _solve_kissat(n, clauses):
    num_vars = max(abs(l) for cl in clauses for l in cl)
    with tempfile.NamedTemporaryFile("w", suffix=".cnf", delete=False) as f:
        f.write(f"p cnf {num_vars} {len(clauses)}\n")
        for cl in clauses:
            f.write(" ".join(map(str, cl)) + " 0\n")
        path = f.name
    try:
        res = subprocess.run([KISSAT, "-q", path], capture_output=True, text=True)
    finally:
        os.remove(path)

    if res.returncode == 20:
        return "UNSAT", None
    if res.returncode != 10:
        return "ERROR", None

    true_vars = []
    for line in res.stdout.splitlines():
        if line.startswith("v"):
            true_vars += [int(x) for x in line.split()[1:] if int(x) > 0]
    return "SAT", decode(n, true_vars)


def solve_clauses(n, clauses, solver):
    """Solve an already-built CNF with the chosen SAT solver."""
    if solver == "kissat":
        return _solve_kissat(n, clauses)

    if solver == "cryptominisat":
        from pycryptosat import Solver
        s = Solver()
        for cl in clauses:
            s.add_clause(cl)
        sat, model = s.solve()
        if not sat:
            return "UNSAT", None
        true_vars = [v for v in range(1, len(model)) if model[v]]
        return "SAT", decode(n, true_vars)

    from pysat.solvers import Solver
    with Solver(name=PYSAT_NAMES[solver], bootstrap_with=clauses) as s:
        if s.solve():
            return "SAT", decode(n, s.get_model())
        return "UNSAT", None


def solve_sat(n, amo, solver, sym=False):
    clauses, _ = build_cnf(n, amo, sym)
    return solve_clauses(n, clauses, solver)


if __name__ == "__main__":
    from nqsat.verify import verify

    for solver in ["cadical", "glucose", "cryptominisat", "kissat"]:
        for enc, fn in AMO.items():
            for n in [4, 8, 50]:
                status, queens = solve_sat(n, fn, solver)
                ok = verify(n, queens) if queens else None
                print(f"{solver:14s} {enc:11s} N={n:3d}  {status:6s} verify={ok}")
