# Experimental protocol

All methods solve the same feasibility problem (place N non-attacking queens)
under the same rules, so that timings are comparable.

- **Threads:** 1 for every solver (Gurobi `Threads=1`, CPLEX CP `Workers=1`,
  CP-SAT `num_workers=1`; the SAT solvers are single-threaded).
- **Time limit:** fixed per run, recorded with the results (the reference paper uses 3600 s).
- **Memory limit:** 80% of physical RAM per run, enforced by the runner.
  Exceeding it is reported as `MO`, never silently dropped.
- **Timed quantity:** model/encoding construction plus solving (`t_total`),
  with `t_encode` and `t_solve` also recorded separately.
- **Isolation:** every run is a separate process, so a crash or memory blow-up
  cannot affect other runs.
- **Correctness:** every returned solution is checked by the independent
  `verify()` in `src/nqsat/verify.py`, regardless of which solver produced it.
- **Status codes:** `SAT`, `UNSAT`, `TO` (time out), `MO` (memory out), `ERR`
  (see `src/nqsat/status.py`).
- **Repetitions:** several seeds where randomness applies; the median is reported.
- **Machine and versions:** see `results/environment.md`.
