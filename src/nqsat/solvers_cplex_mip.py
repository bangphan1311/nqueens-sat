from docplex.mp.model import Model


def solve_cplex_mip(n, time_limit=60):
    m = Model(name="nqueens")
    m.context.cplex_parameters.threads = 1
    m.set_time_limit(time_limit)

    x = m.binary_var_matrix(n, n, name="x")

    for r in range(n):
        m.add_constraint(m.sum(x[r, c] for c in range(n)) == 1)
    for c in range(n):
        m.add_constraint(m.sum(x[r, c] for r in range(n)) <= 1)
    for d in range(-(n - 1), n):
        cells = [(r, r - d) for r in range(n) if 0 <= r - d < n]
        if len(cells) > 1:
            m.add_constraint(m.sum(x[r, c] for r, c in cells) <= 1)
    for s in range(0, 2 * n - 1):
        cells = [(r, s - r) for r in range(n) if 0 <= s - r < n]
        if len(cells) > 1:
            m.add_constraint(m.sum(x[r, c] for r, c in cells) <= 1)

    sol = m.solve()

    if sol is not None:
        queens = []
        for r in range(n):
            for c in range(n):
                if x[r, c].solution_value > 0.5:
                    queens.append(c)
                    break
        return "SAT", queens

    status = m.get_solve_status()
    if status is not None and "infeasible" in str(status).lower():
        return "UNSAT", None
    return "TIMEOUT", None


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from nqsat.verify import verify

    for n in [4, 8, 50, 200]:
        status, queens = solve_cplex_mip(n, time_limit=30)
        ok = verify(n, queens) if queens else None
        print(f"N={n:4d}  status={status:8s}  verify={ok}")
