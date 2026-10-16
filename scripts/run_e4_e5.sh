#!/bin/bash
cd ~/nqueens-sat
echo "START $(date)"
.venv/bin/python -u experiments/run_all.py --ns 100 200 300 500 --reps 3 --timeout 300 --mem-gb 5 --encs commander product --out results/e4_vm.csv
echo "E4 DONE $(date)"
.venv/bin/python -u experiments/run_all.py --ns 50 100 200 --reps 3 --timeout 300 --mem-gb 5 --encs commander --solvers glucose cadical --out results/e5_nosym.csv
.venv/bin/python -u experiments/run_all.py --ns 50 100 200 --reps 3 --timeout 300 --mem-gb 5 --encs commander --solvers glucose cadical --sym --out results/e5_sym.csv
echo "ALL DONE $(date)"
