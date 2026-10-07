import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from pysat.solvers import Solver

from nqsat import amo as A
from nqsat.encode import build_cnf, decode, var

ENC = {
    "pairwise": A.amo_pairwise,
    "seqcounter": A.amo_seqcounter,
    "bitwise": A.amo_bitwise,
    "commander": A.amo_commander,
    "product": A.amo_product,
}
KNOWN = {4: 2, 5: 10, 6: 4, 7: 40, 8: 92, 9: 352}


def all_solutions(n, amo, sym):
    clauses, _ = build_cnf(n, amo, sym)
    sols = set()
    with Solver(name="glucose4", bootstrap_with=clauses) as s:
        while s.solve():
            q = tuple(decode(n, s.get_model()))
            sols.add(q)
            s.add_clause([-var(n, r, q[r]) for r in range(n)])
    return sols


for n in (2, 3):
    for name, fn in ENC.items():
        assert not all_solutions(n, fn, False), f"{name} n={n} should be UNSAT"
print("N=2,3: UNSAT for all encodings")

for n in range(4, 10):
    base = all_solutions(n, ENC["pairwise"], False)
    assert len(base) == KNOWN[n], (n, len(base))
    expected = {q for q in base if q[0] <= (n - 1) // 2}
    for name, fn in ENC.items():
        assert all_solutions(n, fn, False) == base, f"{name} n={n}: full set differs"
        assert all_solutions(n, fn, True) == expected, f"{name} n={n}: sym set differs"
    print(f"N={n}: {len(base)} solutions, {len(expected)} with symmetry breaking, all 5 encodings agree")
print("ALL OK")
