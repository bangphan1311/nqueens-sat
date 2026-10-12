import json
import os
import resource
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

SAT_SOLVERS = ["cadical", "glucose", "cryptominisat", "kissat"]
BASELINES = {
    "cpsat": ("nqsat.solvers_cpsat", "solve_cpsat"),
    "gurobi": ("nqsat.solvers_gurobi", "solve_gurobi"),
    "cplex_mip": ("nqsat.solvers_cplex_mip", "solve_cplex_mip"),
    "cplex_cp": ("nqsat.solvers_cplex_cp", "solve_cplex_cp"),
}
STATUS = {"SAT": "SAT", "UNSAT": "UNSAT", "TIMEOUT": "TO", "ERROR": "ERR"}


def main():
    solver, enc = sys.argv[1], sys.argv[2]
    n, tl, mem_gb = int(sys.argv[3]), float(sys.argv[4]), float(sys.argv[5])
    limit = int(mem_gb * 1024 ** 3)
    resource.setrlimit(resource.RLIMIT_AS, (limit, limit))

    out = {"status": "ERR", "nvars": 0, "nclauses": 0, "t_encode": 0.0, "t_solve": 0.0}
    try:
        from nqsat.verify import verify
        if solver in SAT_SOLVERS:
            from nqsat import solvers_sat as S
            from nqsat.encode import build_cnf
            t0 = time.perf_counter()
            clauses, top = build_cnf(n, S.AMO[enc])
            out["t_encode"] = time.perf_counter() - t0
            out["nvars"], out["nclauses"] = top, len(clauses)
            t1 = time.perf_counter()
            status, queens = S.solve_clauses(n, clauses, solver)
            out["t_solve"] = time.perf_counter() - t1
        else:
            import importlib
            mod, fn = BASELINES[solver]
            f = getattr(importlib.import_module(mod), fn)
            t1 = time.perf_counter()
            status, queens = f(n, time_limit=tl)
            out["t_solve"] = time.perf_counter() - t1
        status = STATUS.get(status, "ERR")
        if status == "SAT" and not verify(n, queens):
            status = "ERR"
        out["status"] = status
    except MemoryError:
        out["status"] = "MO"
    except Exception as e:
        out["status"] = "ERR"
        out["error"] = repr(e)[:200]
    print("RESULT:" + json.dumps(out))


if __name__ == "__main__":
    main()
