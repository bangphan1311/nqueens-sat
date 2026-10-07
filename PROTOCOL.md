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

## Measurement details (run_all.py)

- Default limit is 120 s per run. A run that finishes but whose `t_total` exceeds
  the limit is recorded as `TO`.
- `t_encode` and `t_solve` are separate for the SAT solvers. For the baselines the
  model build and the solve are one call, so only `t_total` is recorded.
- Kissat's `t_solve` includes writing the DIMACS file and starting the process.
- Memory is the resident memory of the whole process group (so Kissat is counted),
  polled every 0.2 s. Peak is stored in `max_rss_mb`.
- Once a configuration fails (`TO`, `MO` or `ERR`) at some N, larger N are recorded
  as `SKIP` and not run.
- Plain N-Queens is deterministic, so repetitions only measure timing noise.

## Repetitions and seeds

- Repetition 1 uses the original clause order. Repetitions >= 2 shuffle the clause
  order with `random.Random(rep)`; the shuffle is not part of the timed quantity
  (`t_total = t_encode + t_solve`). The median over repetitions is reported.
- For the baselines, repetitions only measure timing noise (their models are fixed).
- A configuration is skipped for larger N only when every repetition at some N failed
  (`TO`, `MO` or `ERR`), or when a memory-out occurred (deterministic).
