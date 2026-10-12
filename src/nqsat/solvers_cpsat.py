from ortools.sat.python import cp_model


def solve_cpsat(n, time_limit=60):
    model = cp_model.CpModel()
    queen = [model.NewIntVar(0, n - 1, f"q{r}") for r in range(n)]

    model.AddAllDifferent(queen)
    model.AddAllDifferent([queen[r] + r for r in range(n)])
    model.AddAllDifferent([queen[r] - r for r in range(n)])

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_workers = 1

    result = solver.Solve(model)
    if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return "SAT", [solver.Value(queen[r]) for r in range(n)]
    elif result == cp_model.INFEASIBLE:
        return "UNSAT", None
    return "TIMEOUT", None


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from nqsat.verify import verify

    for n in [4, 8, 50, 200]:
        status, queens = solve_cpsat(n, time_limit=30)
        ok = verify(n, queens) if queens else None
        print(f"N={n:4d}  status={status:8s}  verify={ok}")


def solve_cpsat_bool(n, time_limit=60):
    model = cp_model.CpModel()
    x = [[model.NewBoolVar(f"x{r}_{c}") for c in range(n)] for r in range(n)]

    for r in range(n):
        model.AddExactlyOne(x[r])
    for c in range(n):
        model.AddExactlyOne([x[r][c] for r in range(n)])
    for d in range(-(n - 1), n):
        cells = [x[r][r - d] for r in range(n) if 0 <= r - d < n]
        model.AddAtMostOne(cells)
    for s in range(0, 2 * n - 1):
        cells = [x[r][s - r] for r in range(n) if 0 <= s - r < n]
        model.AddAtMostOne(cells)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 1

    result = solver.Solve(model)
    if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        queens = []
        for r in range(n):
            for c in range(n):
                if solver.Value(x[r][c]):
                    queens.append(c)
                    break
        return "SAT", queens
    elif result == cp_model.INFEASIBLE:
        return "UNSAT", None
    return "TIMEOUT", None
