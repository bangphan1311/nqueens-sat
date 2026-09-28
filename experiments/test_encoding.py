import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pysat.solvers import Solver
from nqsat.amo import amo_pairwise
from nqsat.encode import build_cnf, decode
from nqsat.verify import verify

KNOWN = {1: 1, 2: 0, 3: 0, 4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352, 10: 724}


def count_solutions(n, amo):
    clauses, top = build_cnf(n, amo)
    count, all_ok = 0, True
    with Solver(name="glucose4", bootstrap_with=clauses) as s:
        while s.solve():
            model = s.get_model()
            if not verify(n, decode(n, model)):
                all_ok = False
          
            s.add_clause([-v for v in model if 0 < v <= n * n])
            count += 1
    return count, all_ok


if __name__ == "__main__":
    for n, expected in KNOWN.items():
        got, ok = count_solutions(n, amo_pairwise)
        status = "OK " if (got == expected and ok) else "LOI"
        print(f"[{status}] N={n:2d}  dem={got:4d}  ky vong={expected:4d}  verify={ok}")
