# N-Queens benchmark analysis

- Input files: 7
- Total data records read: 412
- Dataset summaries remain separate; Windows, VM and AWS runtimes must not be pooled into one ranking.
- Runtime medians use SAT rows only; rows with an explicit false verification are excluded.
- SKIP is counted separately and is not treated as an independent timeout.
- t_total includes worker-process startup and other worker overhead.

## Inputs
- `results/e1_sizes.csv`
- `results/e2_encoding_glucose.csv`
- `results/e2_windows_glucose.csv`
- `results/e4_vm.csv`
- `results/e5_nosym.csv`
- `results/e5_sym.csv`
- `results/large_commander_product.csv`

## E1: CNF encoding sizes

E1 measures the number of variables and clauses; it does not measure solver runtime.

| N | Encoding | Status | Variables | Clauses |
|---:|---|---|---:|---:|
| 4 | bitwise | OK | 44 | 116 |
| 4 | commander | OK | 26 | 104 |
| 4 | pairwise | OK | 16 | 84 |
| 4 | product | OK | 84 | 160 |
| 4 | seqcounter | OK | 58 | 116 |
| 8 | bitwise | OK | 170 | 724 |
| 8 | commander | OK | 146 | 618 |
| 8 | pairwise | OK | 64 | 744 |
| 8 | product | OK | 280 | 704 |
| 8 | seqcounter | OK | 274 | 604 |
| 16 | bitwise | OK | 568 | 3924 |
| 16 | commander | OK | 682 | 3052 |
| 16 | pairwise | OK | 256 | 6352 |
| 16 | product | OK | 864 | 2856 |
| 16 | seqcounter | OK | 1186 | 2732 |
| 32 | bitwise | OK | 1846 | 19796 |
| 32 | commander | OK | 2956 | 13290 |
| 32 | pairwise | OK | 1024 | 52640 |
| 32 | product | OK | 2796 | 11928 |
| 32 | seqcounter | OK | 4930 | 11596 |
| 50 | bitwise | OK | 4032 | 57240 |
| 50 | commander | OK | 7354 | 33420 |
| 50 | pairwise | OK | 2500 | 203450 |
| 50 | product | OK | 5954 | 29430 |
| 50 | seqcounter | OK | 12202 | 28912 |
| 64 | bitwise | OK | 6132 | 95572 |
| 64 | commander | OK | 11958 | 55022 |
| 64 | pairwise | OK | 4096 | 428864 |
| 64 | product | OK | 8968 | 47448 |
| 64 | seqcounter | OK | 20098 | 47756 |
| 80 | bitwise | OK | 9234 | 168180 |
| 80 | commander | OK | 18782 | 86646 |
| 80 | pairwise | OK | 6400 | 840720 |
| 80 | product | OK | 13220 | 74584 |
| 80 | seqcounter | OK | 31522 | 75052 |
| 100 | bitwise | OK | 13674 | 269020 |
| 100 | commander | OK | 29502 | 136560 |
| 100 | pairwise | OK | 10000 | 1646900 |
| 100 | product | OK | 19492 | 116672 |
| 100 | seqcounter | OK | 49402 | 117812 |

## Status totals by input file and N

| Dataset | N | OK | SAT | TO | MO | ERR | UNSAT | SKIP |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| e1_sizes.csv | 4 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 8 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 16 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 32 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 50 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 64 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 80 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e1_sizes.csv | 100 | 5 | 0 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 16 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 32 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 50 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_encoding_glucose.csv | 64 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_windows_glucose.csv | 16 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_windows_glucose.csv | 32 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_windows_glucose.csv | 50 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e2_windows_glucose.csv | 64 | 0 | 15 | 0 | 0 | 0 | 0 | 0 |
| e4_vm.csv | 100 | 0 | 39 | 0 | 0 | 0 | 0 | 0 |
| e4_vm.csv | 200 | 0 | 39 | 0 | 0 | 0 | 0 | 0 |
| e4_vm.csv | 300 | 0 | 36 | 1 | 0 | 0 | 0 | 2 |
| e4_vm.csv | 500 | 0 | 36 | 0 | 0 | 0 | 0 | 3 |
| e5_nosym.csv | 50 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_nosym.csv | 100 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_nosym.csv | 200 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_sym.csv | 50 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_sym.csv | 100 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| e5_sym.csv | 200 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| large_commander_product.csv | 500 | 0 | 27 | 1 | 0 | 0 | 0 | 2 |
| large_commander_product.csv | 1000 | 0 | 24 | 1 | 0 | 0 | 0 | 5 |
