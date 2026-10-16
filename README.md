# N-Queens SAT Benchmark

An empirical study of CNF encodings and exact solvers for the N-Queens
feasibility problem. The project compares encoding size, solver runtime,
formulations, symmetry breaking, and execution environments.

A smaller CNF does not necessarily solve faster. Encoding-size results
and runtime measurements are therefore treated as separate experiments.

## What is compared

- **CNF encodings:** pairwise, sequential counter, bitwise, commander,
  and product.
- **SAT solvers:** CaDiCaL, Glucose, CryptoMiniSat, and Kissat.
- **Exact-solver baselines:** CP-SAT, Boolean CP-SAT, Gurobi MIP,
  CPLEX MIP, and CPLEX CP.
- **Symmetry breaking:** selected configurations with and without it.
- **Environments:** Linux VM, separate Windows E2 runs, and AWS EC2.

See [PROTOCOL.md](PROTOCOL.md) for experiment configurations,
measurement rules, limits, and interpretation caveats.

## Repository layout

| Path | Purpose |
|---|---|
| `src/nqsat/` | Encodings, solver adapters, status handling, verification |
| `experiments/` | Experiment runners, analysis, checks, figure generation |
| `scripts/` | Experiment orchestration and CPLEX setup helper |
| `results/` | Raw benchmark CSVs, logs, environment records, summaries |
| `results/exploratory/` | Preliminary pilot/scout results |
| `results/analysis/` | Derived tables and analysis report |
| `figures/` | Exported PDF/PNG figures and plotted-data CSVs |
| `paper/` | Reusable LaTeX fragments for models and complexity tables |
| `PROTOCOL.md` | Experimental methodology and dataset documentation |

## Environment and setup

Python 3.10 or later is required. A C compiler and `make` may be needed
for SAT-solver binaries. Gurobi and CPLEX require suitable installations
and licenses.

### Python environment

For a fresh checkout, create the environment and install locked
dependencies:

    uv sync --locked

**Caution:** the established benchmark VM's `.venv` contains a manually
patched CPLEX library. Running `uv sync` there can replace that library.
Do not resynchronize this existing environment casually.

Use the configured interpreter directly on that machine:

    .venv/bin/python --version
    .venv/bin/python experiments/run_all.py --help

This avoids implicit environment synchronization by `uv run`.
Solver binaries and license files are machine-specific and should not
be committed.

### Plotting environment

Figure generation needs Matplotlib. Keep it in a separate environment
if the project `.venv` must retain the patched CPLEX installation.
The figure script reads CSVs only; it does not launch solvers.

To generate a preview without overwriting tracked figures:

    mkdir -p /tmp/nqsat-figures
    ~/figvenv/bin/python experiments/make_figures.py \
      --results results --out /tmp/nqsat-figures

Adjust the plotting interpreter path if needed. Using `--out figures`
instead will overwrite the repository's figure and `data_*.csv` outputs.

## Experiment datasets

| Experiment | Dataset | Purpose |
|---|---|---|
| E1 | `results/e1_sizes.csv` | Variable and clause counts; no solving |
| E2 Linux | `results/e2_encoding_glucose.csv` | Encoding comparison using Glucose |
| E2 Windows | `results/e2_windows_glucose.csv` | Separate Windows measurements |
| E4 | `results/e4_vm.csv` | SAT configurations and exact-solver baselines |
| E5, no symmetry | `results/e5_nosym.csv` | Selected configurations without symmetry breaking |
| E5, symmetry | `results/e5_sym.csv` | Corresponding configurations with symmetry breaking |
| AWS large-N | `results/large_commander_product.csv` | Larger instances on a separate AWS environment |

See `PROTOCOL.md` for detailed configurations and
`results/environment_vm.md` and `results/environment_aws.md` for
the recorded machine environments.

Historical CSVs and logs are experimental evidence. Rerunning an
experiment creates new measurements; it should not silently replace
the recorded results. Do not compare absolute runtime across different
machines as if the environment were controlled.

## Running experiments

Inspect the available options before launching a run:

    .venv/bin/python experiments/run_all.py --help
    .venv/bin/python experiments/e1_sizes.py --help

The E4/E5 script invokes the configured project interpreter:

    bash scripts/run_e4_e5.sh

**Warning:** E4/E5 writes experiment outputs. Review the script and
output paths before running it, especially when preserving the
recorded results. Do not rerun benchmarks merely to inspect the
repository or regenerate figures.

The exact original invocation for Linux E2 was not retained in a
dedicated experiment log. Consult `PROTOCOL.md` for the documented
configuration rather than assuming undocumented command-line options.

## Analysis and figures

- `experiments/analyze.py` generates summaries from result CSVs.
- `experiments/make_figures.py` creates PDF/PNG figures and matching
  `data_*.csv` files from the recorded datasets.
- `results/analysis/` contains derived tables and the analysis report.
- `figures/data_*.csv` records the data used by the exported figures.

Inspect a script's help output before running it. Analysis and figure
generation should not require rerunning a solver.

## Correctness and methodology

The implementation includes solution verification and encoding
complexity checks. Results distinguish successful solves, timeouts,
memory-outs, and skipped runs. A `SKIP` is not a solver outcome.

Runtime includes the timing scope defined by the experiment runner;
this may include process startup and model or instance preparation.
Interpret successful-run summaries together with failure outcomes.
See `PROTOCOL.md` for further methodological details and limitations.

## Licensing

Third-party solvers have their own licensing terms. Gurobi and CPLEX
may require academic or commercial licenses depending on the
installation and use. Their libraries, license files, and local
solver binaries are not bundled with this repository.

## External solver setup

### Kissat

The default binary path is `~/kissat/build/kissat`.

```bash
git clone --depth 1 https://github.com/arminbiere/kissat.git ~/kissat
cd ~/kissat
./configure
make -j4
cd ~/nqueens-sat
```

### Gurobi

Install Gurobi and configure a valid license. For a license at
`~/.gurobi/gurobi.lic`, set:

```bash
export GRB_LICENSE_FILE="$HOME/.gurobi/gurobi.lic"
```

### CPLEX

Install IBM ILOG CPLEX Optimization Studio with a suitable license.
Check the configured installation before patching the Python library:

```bash
scripts/setup_cplex_license.sh --check
scripts/setup_cplex_license.sh
```

The Studio path is controlled by `CPLEX_STUDIO`. Check the CP Optimizer
binary path in `src/nqsat/solvers_cplex_cp.py`. License files must not
be committed. On the benchmark VM, `.venv` contains a patched CPLEX
library; avoid running `uv sync` there because it may replace the patch.

## Tests

Run these checks when validating code changes; they are not benchmarks:

```bash
.venv/bin/python -m compileall -q src experiments
.venv/bin/python experiments/smoke_test.py
.venv/bin/python experiments/test_encoding.py
.venv/bin/python experiments/test_sym.py
.venv/bin/python experiments/test_runner_resume.py
```
