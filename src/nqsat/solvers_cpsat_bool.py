from ortools.sat.python import cp_model


def solve_cpsat_bool(n, time_limit=60):
    """CP-SAT with the Boolean model (same variables as the SAT encoding)."""
    m = cp_model.CpModel()
    x = [[m.NewBoolVar(f"x_{r}_{c}") for c in range(n)] for r in range(n)]

    for r in range(n):
        m.AddExactlyOne(x[r])
    for c in range(n):
        m.AddAtMostOne([x[r][c] for r in range(n)])
    for d in range(-(n - 1), n):
        cells = [x[r][r - d] for r in range(n) if 0 <= r - d < n]
        if len(cells) > 1:
            m.AddAtMostOne(cells)
    for s in range(2 * n - 1):
        cells = [x[r][s - r] for r in range(n) if 0 <= s - r < n]
        if len(cells) > 1:
            m.AddAtMostOne(cells)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 1
    st = solver.Solve(m)

    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        queens = [next(c for c in range(n) if solver.BooleanValue(x[r][c])) for r in range(n)]
        return "SAT", queens
    if st == cp_model.INFEASIBLE:
        return "UNSAT", None
    return "TIMEOUT", None


if __name__ == "__main__":
    import os
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from nqsat.verify import verify

    for n in [4, 8, 50, 200]:
        status, queens = solve_cpsat_bool(n, time_limit=30)
        ok = verify(n, queens) if queens else None
        print(f"N={n:4d}  status={status:8s}  verify={ok}")
