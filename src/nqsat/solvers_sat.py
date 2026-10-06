import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nqsat import amo as A
from nqsat.encode import build_cnf, decode

AMO = {
    "pairwise": A.amo_pairwise,
    "seqcounter": A.amo_seqcounter,
    "bitwise": A.amo_bitwise,
    "commander": A.amo_commander,
    "product": A.amo_product,
}

PYSAT_NAMES = {"cadical": "cadical153", "glucose": "glucose4"}


def solve_sat(n, amo, solver):
    clauses, _ = build_cnf(n, amo)

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


if __name__ == "__main__":
    from nqsat.verify import verify

    for solver in ["cadical", "glucose", "cryptominisat"]:
        for enc, fn in AMO.items():
            for n in [4, 8, 50]:
                status, queens = solve_sat(n, fn, solver)
                ok = verify(n, queens) if queens else None
                print(f"{solver:14s} {enc:11s} N={n:3d}  {status:6s} verify={ok}")
