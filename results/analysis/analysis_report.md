# N-Queens benchmark analysis

- Input files: 5
- Total data records read: 312
- Raw input files are kept separate in summaries; Windows, VM and AWS times must not be pooled as one runtime ranking.
- Runtime medians use SAT rows only; rows with an explicit false verification are excluded.
- SKIP is counted separately and is not treated as an independent timeout.
- t_total includes process startup according to the runner's timing protocol.

## Inputs
- `results/e2_encoding_glucose.csv`
- `results/e4_vm.csv`
- `results/e5_nosym.csv`
- `results/e5_sym.csv`
- `results/large_commander_product.csv`

## Status totals by input file and N

| Dataset | N | SAT | TO | MO | ERR | UNSAT | SKIP |
|---|---:|---:|---:|---:|---:|---:|---:|
| e2_encoding_glucose.csv | 16 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 32 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 50 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 64 | 15 | 0 | 0 | 0 | 0 | 0 |
| e4_vm.csv | 100 | 39 | 0 | 0 | 0 | 0 | 0 |
| e4_vm.csv | 200 | 39 | 0 | 0 | 0 | 0 | 0 |
| e4_vm.csv | 300 | 36 | 1 | 0 | 0 | 0 | 2 |
| e4_vm.csv | 500 | 36 | 0 | 0 | 0 | 0 | 3 |
| e5_nosym.csv | 50 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_nosym.csv | 100 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_nosym.csv | 200 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_sym.csv | 50 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_sym.csv | 100 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_sym.csv | 200 | 6 | 0 | 0 | 0 | 0 | 0 |
| large_commander_product.csv | 500 | 27 | 1 | 0 | 0 | 0 | 2 |
| large_commander_product.csv | 1000 | 24 | 1 | 0 | 0 | 0 | 5 |
