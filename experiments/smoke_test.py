from pysat.solvers import Solver

clauses = [[1, 2], [-1, 2], [-2, 3]]

for name in ["cadical153", "glucose4", "minisat22"]:
    with Solver(name=name, bootstrap_with=clauses) as s:
        print(name, s.solve(), s.get_model())
