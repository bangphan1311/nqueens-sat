# N-Queens SAT benchmark

Benchmark of SAT encodings and solvers on the N-Queens feasibility problem
(place N non-attacking queens on an N x N board). N-Queens has a direct O(N)
construction, so the goal is to compare formulations and solvers, not to find
the best way to solve N-Queens.

## What is compared

- **SAT solvers:** CaDiCaL (PySAT `cadical153`), Glucose 4 (PySAT `glucose4`),
  CryptoMiniSat (`pycryptosat`), Kissat (external binary, called through a DIMACS file).
- **At-most-one encodings:** pairwise, sequential counter (`seqcounter`),
  binary (`bitwise`), commander, product. See `src/nqsat/amo.py`.
- **Baselines:** OR-Tools CP-SAT (AllDifferent model and Boolean model), Gurobi (MIP),
  CPLEX MIP, CPLEX CP Optimizer.
- Every solution returned by any solver is checked by the independent verifier
  `src/nqsat/verify.py`. A solution that fails the check is recorded as `ERR`.

## Repository layout

| Path | Content |
|---|---|
| `src/nqsat/` | encodings (`amo.py`, `encode.py`), solver wrappers (`solvers_*.py`), `worker.py`, `verify.py`, `status.py` |
| `experiments/run_all.py` | main benchmark runner (one worker process per run) |
| `experiments/analyze.py` | summarises result CSVs into `results/analysis/` |
| `experiments/e1_sizes.py`, `e2_encoding_glucose.py` | E1 (CNF size) and the Windows E2 script |
| `experiments/test_*.py`, `smoke_test.py` | correctness tests |
| `scripts/` | `run_e4_e5.sh`, `setup_cplex_license.sh` |
| `results/` | raw CSVs and logs of every reported experiment |
| `PROTOCOL.md` | exact measurement protocol; read it before interpreting any number |

## Setup (Linux x86_64)

Requirements: Python >= 3.10, [uv](https://docs.astral.sh/uv/), a C compiler and `make`.

1. Python environment: `uv sync`
2. Kissat (expected at `~/kissat/build/kissat`, see `KISSAT` in `src/nqsat/solvers_sat.py`):
```bash
   git clone --depth 1 https://github.com/arminbiere/kissat.git ~/kissat
   cd ~/kissat && ./configure && make -j4
```
3. Gurobi: put your own licence at `~/.gurobi/gurobi.lic` and run
   `export GRB_LICENSE_FILE=$HOME/.gurobi/gurobi.lic`.
4. CPLEX: the pip package is the Community Edition (about 1000 variables).
   Install IBM CPLEX Studio with a valid academic licence, then replace the library:
```bash
   scripts/setup_cplex_license.sh --check   # report only
   scripts/setup_cplex_license.sh           # patch
```
   The Studio path is set by `CPLEX_STUDIO` (default `~/ibm/ILOG/CPLEX_Studio2211`).
   The CP Optimizer binary path is set in `src/nqsat/solvers_cplex_cp.py`.

Gurobi and CPLEX academic licences are for non-commercial use. Check their terms
before installing on a new machine. Licence files are git-ignored; never commit them.

**uv and the CPLEX patch:** `uv sync` recreates the Community library, so patch again
after it. To make sure uv never touches a patched environment, run commands with
`.venv/bin/python` instead of `uv run` (or use `uv run --no-sync`).

## Tests

```bash
.venv/bin/python -m compileall -q src experiments
.venv/bin/python experiments/smoke_test.py
.venv/bin/python experiments/test_encoding.py      # known solution counts, N = 1..10, 5 encodings
.venv/bin/python experiments/test_sym.py           # symmetry breaking; ends with ALL OK
.venv/bin/python experiments/test_runner_resume.py # resume and skip logic of run_all.py
```

## Running experiments

```bash
.venv/bin/python -u experiments/run_all.py --ns 100 200 --reps 3 --timeout 300 --mem-gb 5 \
    --encs commander product --solvers glucose gurobi --out results/demo.csv
```

| Option | Meaning | Default |
|---|---|---|
| `--ns` | board sizes | 8 16 32 50 100 200 300 500 1000 |
| `--reps` | repetitions per configuration | 3 |
| `--timeout` | seconds per run | 300 |
| `--mem-gb` | address-space limit of a run (`RLIMIT_AS`) | 5 |
| `--solvers` | `cadical glucose cryptominisat kissat cpsat cpsat_bool gurobi cplex_mip cplex_cp` | all |
| `--encs` | SAT encodings: `pairwise seqcounter bitwise commander product` | all |
| `--sym` | symmetry breaking (SAT solvers) | off |
| `--out` | output CSV | `results/results.csv` |

Running the same command again resumes from the CSV and skips finished runs.

| Experiment | How to reproduce | Output |
|---|---|---|
| E1 CNF sizes | `.venv/bin/python experiments/e1_sizes.py` | `results/e1_sizes.csv` |
| E2 encodings, Glucose (Linux) | `--ns 16 32 50 64 --solvers glucose --out results/e2_encoding_glucose.csv` (the original command was not saved; this is the same configuration) | `results/e2_encoding_glucose.csv` |
| E2 (Windows) | `experiments/e2_encoding_glucose.py` | `results/e2_windows_glucose.csv` |
| E4 solver comparison, E5 symmetry | `scripts/run_e4_e5.sh` | `results/e4_vm.csv`, `e5_nosym.csv`, `e5_sym.csv` |
| Large N on AWS | `--ns 500 1000 --reps 3 --timeout 300 --mem-gb 5 --encs commander product --solvers cadical glucose cryptominisat kissat cpsat cpsat_bool` | `results/large_commander_product.csv` |

The AWS batch was run with an earlier revision of the runner; the encoding list was
restricted by editing it, which is equivalent to `--encs commander product`.
Gurobi and CPLEX were not run on AWS.

## Analysis

```bash
.venv/bin/python experiments/analyze.py results/e1_sizes.csv results/e2_encoding_glucose.csv \
    results/e2_windows_glucose.csv results/e4_vm.csv results/e5_nosym.csv \
    results/e5_sym.csv results/large_commander_product.csv
```

Writes `analysis_report.md`, `encoding_size_summary.csv`, `solver_encoding_summary.csv`
and `status_counts.csv` to `results/analysis/`. Each input file is summarised separately.

## Reading the results

- Columns: `n, solver, encoding, sym, rep, nvars, nclauses, t_encode, t_solve, t_total, status`.
- Status: `SAT`, `UNSAT`, `TO` (timeout), `MO` (memory error), `ERR` (error or failed
  verification), `SKIP` (not run because an earlier repetition 0 timed out or ran out of
  memory for that configuration and N; a skip is not a measured timeout).
- `t_total` is the wall time of the whole worker process, including start-up and imports.
  It is not `t_encode + t_solve`. For Kissat, `t_solve` also includes writing the DIMACS
  file and starting the process.
- The memory limit is `RLIMIT_AS` (virtual address space), not resident memory.
- `rep` numbers the repetitions. It is not a random seed, and the clause order is not
  shuffled. Repetitions only show timing variation between identical runs.
- All solvers run with one thread (see `PROTOCOL.md`).

## Machines

Timings from different machines are never pooled.

- **Linux VM:** Ubuntu 26.04 VM on a laptop with an AMD Ryzen 5 7535HS, 4 vCPU, 7.2 GiB RAM
  (`results/environment.md`). Used for E2 (Linux), E4 and E5.
- **AWS:** EC2 `c5.xlarge`, Intel Xeon Platinum 8275CL, 4 vCPU, 7.5 GiB RAM, Ubuntu 26.04.
  Used for the large-N batch.
- **Windows:** the E2 script run on the Windows laptop that hosts the VM.
