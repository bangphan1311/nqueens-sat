import os
from docplex.cp.model import CpoModel

def solve_cplex_cp(n, time_limit=60):
    m = CpoModel()
    q = [m.integer_var(0, n - 1, name=f"q{r}") for r in range(n)]

    m.add(m.all_diff(q))
    m.add(m.all_diff([q[r] + r for r in range(n)]))
    m.add(m.all_diff([q[r] - r for r in range(n)]))

    cpo_path = os.path.expanduser("~/ibm/ILOG/CPLEX_Studio2211/cpoptimizer/bin/x86-64_linux/cpoptimizer")

    sol = m.solve(TimeLimit=time_limit, Workers=1, LogVerbosity="Quiet", execfile=cpo_path)

    if sol:
        queens = [sol[q[r]] for r in range(n)]
        return "SAT", queens
    if sol.get_solve_status() == "Infeasible":
        return "UNSAT", None
    return "TIMEOUT", None

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from nqsat.verify import verify
    for n in [4, 8, 50, 200]:
        status, queens = solve_cplex_cp(n, time_limit=30)
        ok = verify(n, queens) if queens else None
        print(f"N={n:4d}  status={status:8s}  verify={ok}")
