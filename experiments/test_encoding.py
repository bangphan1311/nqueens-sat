import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pysat.solvers import Solver
from nqsat.amo import AMO_ENCODINGS
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
    for name, amo in AMO_ENCODINGS.items():
        for n, expected in KNOWN.items():
            got, ok = count_solutions(n, amo)
            status = "OK " if (got == expected and ok) else "LOI"
            print(f"[{status}] {name:10s} N={n:2d}  dem={got:4d}  ky vong={expected:4d}  verify={ok}")
    
    print("\n=== Kich thuoc encoding (so bien, so luat) ===")
    print(f"{'N':>4} " + " ".join(f"{name:>22s}" for name in AMO_ENCODINGS))
    for n in [8, 16, 32, 64]:
        row = []
        for name, amo in AMO_ENCODINGS.items():
            clauses, top = build_cnf(n, amo)
            row.append(f"{top:>9d} v {len(clauses):>9d} c")
        print(f"{n:>4} " + " ".join(f"{r:>22s}" for r in row))
