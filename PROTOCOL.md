# Experimental Protocol

## 1. Problem and correctness

All solvers address the same N-Queens feasibility problem: place N queens
on an N x N board so that no two queens attack each other.

For SAT runs, the CNF encoding is constructed before the SAT solver is called.
For baseline solvers, model construction and solving are handled by the
corresponding solver wrapper.

Every SAT solution returned by the main worker is checked again using the
independent verifier in `src/nqsat/verify.py`. A solution that fails verification
is recorded as `ERR`, not `SAT`.

E1 measures encoding size only; it does not solve the resulting instances.

## 2. Solvers and parallelism

The benchmark includes the following SAT solvers:
CaDiCaL, Glucose, CryptoMiniSat, and Kissat.

The baseline methods are:
- OR-Tools CP-SAT
- OR-Tools Boolean CP-SAT
- Gurobi
- CPLEX MIP
- CPLEX CP

The solver wrappers configure the baseline methods to use one thread:
Gurobi (`Threads = 1`), CPLEX MIP (`threads = 1`), CPLEX CP (`Workers = 1`),
and both CP-SAT variants (`num_workers = 1`). The SAT solvers are run in their
standard single-process configuration.

For SAT experiments, the encodings include pairwise, sequential counter,
bitwise, commander, and product. Some experiments use only a subset of these
encodings, as specified below.

## 3. Time and memory limits

### Main runner (`experiments/run_all.py`)

The runner defaults to a 300-second timeout and a 5-GiB memory argument.
Experiments may override these values on the command line; the actual settings
used for each reported experiment are listed in Section 6.

The worker (`src/nqsat/worker.py`) applies the memory argument with
`resource.setrlimit(resource.RLIMIT_AS, ...)`. This limits the worker's virtual
address space, not its measured resident physical memory (RSS). The current
runner does not periodically sample RSS and does not write a `max_rss_mb`
measurement to the result CSV.

A Python `MemoryError` caught by the worker is reported as `MO`. A process
that exits without returning a result may instead be classified by the parent
runner as `MO` or `ERR`, depending on the error output.

For the main runner, the parent process measures wall-clock time around worker
startup and execution. SAT workers are terminated if the parent-side timeout
expires. Baseline solvers also receive the requested solver time limit; the
parent allows an additional 20-second grace period before forcefully terminating
the worker.

### Timing fields

- `t_encode`: time spent building the CNF for SAT runs.
- `t_solve`: elapsed time around the SAT solving function. Depending on the
  SAT backend, this can include solver initialization and loading clauses as
  well as the solve call. For baseline methods, the measured call includes the
  solver wrapper's model construction and solve.
- `t_total`: parent-measured wall-clock time for the worker process, including
  process startup and other worker overhead.

For Kissat, `t_solve` also includes writing the temporary DIMACS file,
starting the Kissat process, reading its output, and cleaning up the temporary
file. It is therefore not a measurement of the solver's internal search time alone.

Consequently, `t_total` should not be assumed to equal exactly
`t_encode + t_solve`. This distinction matters especially for small instances,
where process startup and imports can be a substantial fraction of total time.

The dedicated Windows E2 script has its own runner and a default timeout of
60 seconds per run. Its results must not be treated as if they were collected
with the same process and timing setup as the main Linux runner.

## 4. Repetitions and skipped runs

The main runner labels repetitions using `rep = 0, 1, 2, ...`. The repetition
index is recorded in the CSV, but `run_all.py` does not pass it to the worker
as a random seed and does not itself shuffle the CNF clause order.
Do not describe the main-runner repetitions as seeded clause-order shuffles.

N-Queens feasibility instances are deterministic, but measured wall-clock times
can still vary between runs. For successful repetitions, report the median
rather than relying on a single timing. Always show failures separately.

Status definitions:

- `SAT`: a valid solution was found.
- `UNSAT`: the solver reported that the instance is unsatisfiable.
- `TO`: a timeout was reported or the parent runner reached its timeout.
- `MO`: the worker reported a memory error.
- `ERR`: an unexpected error occurred, or a returned SAT solution failed
  independent verification.
- `SKIP`: the run was deliberately not executed by the runner's skip logic.

`SKIP` is not an independently measured timeout.

In a fresh `run_all.py` sweep, a `TO` or `MO` at repetition 0 marks that
solver/encoding configuration as failed. Subsequent repetitions and larger
instances for that configuration are then recorded as `SKIP`. When continuing
from an existing CSV, a prior `TO` or `MO` for a solver/encoding can also cause
missing runs for that configuration to be skipped. The current main runner
does not apply the same automatic skip rule to `ERR`.

Therefore, distinguish measured `TO`/`MO` outcomes from `SKIP` entries when
counting results. Do not interpret a skipped row as another independent
timeout.

## 5. Analysis and comparison rules

The analysis script summarizes successful (`SAT`) timings separately by input
CSV file. This preserves the distinction between Windows, the local Linux VM,
and AWS experiments.

Do not rank solvers by directly comparing wall-clock times from different
machines. Hardware, operating environment, process startup, library versions,
and solver installations can differ. Compare solver timings primarily within
the same experiment and environment.

Encoding size results, such as variable and clause counts, can be discussed
separately from runtime. E1 is a size experiment, not a solver-runtime
benchmark.

## 6. Experiment configurations and result files

### E1: CNF encoding size

- Script: `experiments/e1_sizes.py`
- Encodings: pairwise, seqcounter, bitwise, commander, product
- N: 4, 8, 16, 32, 50, 64, 80, 100
- Output: `results/e1_sizes.csv`
- Measurement: number of variables and clauses for each encoding
- No SAT solving is performed in E1.

### E2: Glucose encoding comparison

**Linux VM**
- Output: `results/e2_encoding_glucose.csv`
- Five encodings, N = 16, 32, 50, 64, three repetitions
- Results were collected with the main Linux runner.
- The main runner defaults to 300 seconds and 5 GiB unless overridden.
  The original command was not saved in a dedicated experiment log, so these
  defaults should only be reported as the actual settings if no overrides were
  supplied when the run was launched.

**Windows**
- Script: `experiments/e2_encoding_glucose.py`
- Output: `results/e2_windows_glucose.csv`
- Solver: Glucose 4
- Five encodings, N = 16, 32, 50, 64, three repetitions
- Default per-run timeout: 60 seconds
- This is a separate dataset collected with the Windows-specific runner.
  Its timing results are not pooled with the Linux VM results.

### E4: Solver and formulation comparison

- Script: `scripts/run_e4_e5.sh`
- Output: `results/e4_vm.csv`
- Environment: local Linux VM
- N = 100, 200, 300, 500; three repetitions
- Main-runner arguments: `--timeout 300 --mem-gb 5`
- SAT solvers: CaDiCaL, Glucose, CryptoMiniSat, Kissat
- SAT encodings: commander and product
- Baselines: CP-SAT, Boolean CP-SAT, Gurobi, CPLEX MIP, CPLEX CP

A baseline row uses `-` as its encoding label because it does not use a SAT
encoding.

### E5: Symmetry-breaking comparison

- Outputs: `results/e5_nosym.csv` and `results/e5_sym.csv`
- Environment: local Linux VM
- SAT solvers: CaDiCaL and Glucose
- Encoding: commander
- N = 50, 100, 200; three repetitions
- Main-runner arguments: `--timeout 300 --mem-gb 5`
- Comparison: the same solver/encoding/instance settings with and without
  the symmetry-breaking option.

Interpret changes in timing individually for each instance and solver.
Do not claim that symmetry breaking always improves runtime.

### AWS large-N batch

- Output: `results/large_commander_product.csv`
- Environment: AWS EC2, separate from the local Linux VM
- N = 500 and 1000; three repetitions
- Timeout: 300 seconds
- Memory argument: 5 GiB
- SAT solvers: CaDiCaL, Glucose, CryptoMiniSat, Kissat
- SAT encodings: commander and product
- Baselines in this batch: CP-SAT and Boolean CP-SAT

Report this batch separately from local VM results. Do not use cross-machine
runtime comparisons as if they were controlled on identical hardware.

## 7. Environment information

The local VM software and hardware information is documented in
`results/environment_vm.md`, and the AWS machine in `results/environment_aws.md`.
Record Windows environment information separately when reporting results from
that machine.

The raw CSV files and logs are retained to support reproducibility. Summary
statistics should be traceable to the corresponding source CSV, and `SKIP`
entries should remain distinguishable from actual solver outcomes.
