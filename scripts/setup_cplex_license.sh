#!/bin/bash
set -e
STUDIO="${CPLEX_STUDIO:-$HOME/ibm/ILOG/CPLEX_Studio2211}"
SRC="$STUDIO/cplex/bin/x86-64_linux/libcplex2220.so"
VENV="$(dirname "$0")/../.venv"
cp "$SRC" "$VENV/lib/python3.10/site-packages/cplex/_internal/libcplex2220.so"
cp "$SRC" "$VENV/bin/libcplex2220.so"
echo "Da va libcplex2220.so tu $SRC"
