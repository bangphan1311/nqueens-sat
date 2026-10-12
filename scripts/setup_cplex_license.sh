#!/usr/bin/env bash
# Replace the Community-Edition CPLEX library shipped inside the pip package
# with the full library from an IBM CPLEX Studio installation (Academic licence).
#
# Usage:
#   scripts/setup_cplex_license.sh           patch the library
#   scripts/setup_cplex_license.sh --check   only report the state, change nothing
#
# Environment variables (all optional):
#   CPLEX_STUDIO   Studio install dir (default: $HOME/ibm/ILOG/CPLEX_Studio2211)
#   VENV           virtualenv to patch (default: <repo>/.venv)
#
# The script never runs uv, never creates or deletes a virtualenv.
# Running `uv sync` later recreates the Community library, so patch again after it.
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }

MODE="patch"
case "${1:-}" in
  "") ;;
  --check) MODE="check" ;;
  -h|--help) sed -n '2,13p' "$0"; exit 0 ;;
  *) die "unknown argument: $1 (use --check or no argument)" ;;
esac

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV="${VENV:-$REPO/.venv}"
STUDIO="${CPLEX_STUDIO:-$HOME/ibm/ILOG/CPLEX_Studio2211}"
PY="$VENV/bin/python"

[ -x "$PY" ] || die "no Python found at $PY. Create the environment first (uv sync), then run this script."

PLATLIB="$("$PY" -c 'import sysconfig; print(sysconfig.get_paths()["platlib"])')"
INTERNAL="$PLATLIB/cplex/_internal"
[ -d "$INTERNAL" ] || die "the 'cplex' Python package is not installed in $VENV (expected $INTERNAL)."

# The library name depends on the pip package version (e.g. libcplex2220.so).
DEST1="$(ls "$INTERNAL"/libcplex*.so 2>/dev/null | head -n 1 || true)"
[ -n "$DEST1" ] || die "no libcplex*.so found in $INTERNAL."
LIBNAME="$(basename "$DEST1")"
DEST2="$VENV/bin/$LIBNAME"

SRC="$(find "$STUDIO/cplex/bin" -name "$LIBNAME" -type f 2>/dev/null | head -n 1 || true)"
[ -n "$SRC" ] || die "$LIBNAME not found under $STUDIO/cplex/bin.
Install IBM CPLEX Studio (Academic) or set CPLEX_STUDIO to its install directory.
Hint: find \"\$CPLEX_STUDIO\" -name 'libcplex*'"

same() { [ -f "$1" ] && cmp -s "$SRC" "$1"; }

echo "venv    : $VENV"
echo "library : $LIBNAME"
echo "source  : $SRC"
for d in "$DEST1" "$DEST2"; do
  if same "$d"; then echo "status  : patched      $d"
  elif [ -f "$d" ]; then echo "status  : NOT patched  $d"
  else echo "status  : missing      $d"; fi
done

if [ "$MODE" = "check" ]; then exit 0; fi

if same "$DEST1" && same "$DEST2"; then
  echo "Already patched, nothing to do."
  exit 0
fi

cp -f "$SRC" "$DEST1"
cp -f "$SRC" "$DEST2"
same "$DEST1" && same "$DEST2" || die "copy finished but the files differ from the source."
echo "Patched. Verify with: $PY $REPO/src/nqsat/solvers_cplex_mip.py"
