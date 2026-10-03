import gurobipy as gp
from gurobipy import GRB


def solve_gurobi(n, time_limit=60):
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()

    model = gp.Model(env=env)
    model.Params.TimeLimit = time_limit
    model.Params.Threads = 1

    x = model.addVars(n, n, vtype=GRB.BINARY, name="x")

    for r in range(n):
        model.addConstr(gp.quicksum(x[r, c] for c in range(n)) == 1)
    for c in range(n):
        model.addConstr(gp.quicksum(x[r, c] for r in range(n)) <= 1)
    for d in range(-(n - 1), n):
        cells = [(r, r - d) for r in range(n) if 0 <= r - d < n]
        if len(cells) > 1:
            model.addConstr(gp.quicksum(x[r, c] for r, c in cells) <= 1)
    for s in range(0, 2 * n - 1):
        cells = [(r, s - r) for r in range(n) if 0 <= s - r < n]
        if len(cells) > 1:
            model.addConstr(gp.quicksum(x[r, c] for r, c in cells) <= 1)

    model.optimize()

    if model.Status == GRB.OPTIMAL or (model.Status == GRB.TIME_LIMIT and model.SolCount > 0):
        queens = []
        for r in range(n):
            for c in range(n):
                if x[r, c].X > 0.5:
                    queens.append(c)
                    break
        status = "SAT" if model.Status == GRB.OPTIMAL else "SAT"
        return status, queens
    elif model.Status == GRB.INFEASIBLE:
        return "UNSAT", None
    return "TIMEOUT", None


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from nqsat.verify import verify

    for n in [4, 8, 50, 200]:
        status, queens = solve_gurobi(n, time_limit=30)
        ok = verify(n, queens) if queens else None
        print(f"N={n:4d}  status={status:8s}  verify={ok}")
