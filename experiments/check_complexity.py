#!/usr/bin/env python3
"""Check closed-form N-Queens CNF sizes against recorded CSV results.

The formulas implement the AMO variants described in src/nqsat/amo.py and
count row/column ALO clauses as in src/nqsat/encode.py. This is a pure-Python
check; it does not import PySAT or launch a solver.

Usage:
  .venv/bin/python experiments/check_complexity.py
  .venv/bin/python experiments/check_complexity.py --table
  .venv/bin/python experiments/check_complexity.py --results results

A row is checked whenever it has a recognized encoding and recorded nvars and
nclauses. Its solver status is deliberately irrelevant: a timed-out solve can
still have a fully encoded CNF whose size should be checked.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]


def ceil_log2(k: int) -> int:
    return (k - 1).bit_length() if k >= 2 else 0


def choose2(k: int) -> int:
    return k * (k - 1) // 2


# Return (auxiliary variables, clauses) for one AMO block on k literals.
def pairwise(k: int) -> tuple[int, int]:
    return 0, choose2(k)


def seqcounter(k: int) -> tuple[int, int]:
    return (0, 0) if k <= 1 else (k - 1, 3 * k - 4)


def bitwise(k: int) -> tuple[int, int]:
    if k <= 1:
        return 0, 0
    if k == 2:  # implementation special-cases two literals as one clause
        return 0, 1
    b = ceil_log2(k)
    return b, k * b


def commander(k: int, group_size: int = 3) -> tuple[int, int]:
    if k <= 1:
        return 0, 0
    if k <= group_size:
        return pairwise(k)
    full, rem = divmod(k, group_size)
    aux = clauses = 0
    groups = [group_size] * full + ([rem] if rem else [])
    for group_len in groups:
        if group_len >= 2:
            aux += 1
            clauses += choose2(group_len) + group_len + 1
    next_level = full + (1 if rem else 0)
    a, c = commander(next_level, group_size)
    return aux + a, clauses + c


def product(k: int) -> tuple[int, int]:
    if k <= 1:
        return 0, 0
    p = math.isqrt(k - 1) + 1  # ceil(sqrt(k))
    q = (k + p - 1) // p      # ceil(k/p)
    return p + q, choose2(p) + choose2(q) + 2 * k


AMO: dict[str, Callable[[int], tuple[int, int]]] = {
    "pairwise": pairwise,
    "seqcounter": seqcounter,
    "bitwise": bitwise,
    "commander": commander,
    "product": product,
}

CSV_NAMES = (
    "e1_sizes.csv",
    "e2_encoding_glucose.csv",
    "e2_windows_glucose.csv",
    "e4_vm.csv",
    "e5_nosym.csv",
    "e5_sym.csv",
    "large_commander_product.csv",
)


def constraint_line_lengths(n: int) -> list[int]:
    if n < 1:
        raise ValueError(f"N must be >= 1, got {n}")
    diagonals = [n - abs(d) for d in range(-(n - 1), n)]
    return [n] * (2 * n) + diagonals + diagonals


def expected_size(n: int, encoding: str, sym: bool = False) -> tuple[int, int]:
    """Return total (variables, clauses) for the specified CNF formulation."""
    if n < 1:
        raise ValueError(f"N must be >= 1, got {n}")
    try:
        amo = AMO[encoding]
    except KeyError as exc:
        raise ValueError(f"Unknown AMO encoding: {encoding}") from exc
    aux_total = clause_total = 0
    for length in constraint_line_lengths(n):
        aux, clauses = amo(length)
        aux_total += aux
        clause_total += clauses
    clause_total += 2 * n  # one ALO per row and per column
    if sym:
        # Same clause count as encode.py's left/right symmetry restriction.
        clause_total += n // 2
    return n * n + aux_total, clause_total


def parse_sym(raw: str | None, path: Path, rownum: int) -> bool:
    value = (raw or "0").strip().lower()
    if value in {"", "0", "false", "no", "off", "none"}:
        return False
    if value in {"1", "true", "yes", "on"}:
        return True
    raise ValueError(f"{path}:{rownum}: unrecognized sym value {raw!r}")


def check_csv(path: Path) -> dict[str, int]:
    counts = {
        "rows": 0,
        "checked": 0,
        "mismatches": 0,
        "ignored_non_amo": 0,
        "missing_size": 0,
        "no_cnf": 0,
        "malformed": 0,
    }
    if not path.is_file():
        print(f"ERROR missing required CSV: {path}", file=sys.stderr)
        counts["missing_file"] = 1
        return counts

    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        required = {"n", "encoding", "nvars", "nclauses"}
        headers = set(reader.fieldnames or ())
        if not required.issubset(headers):
            print(
                f"ERROR {path}: missing columns {sorted(required - headers)}",
                file=sys.stderr,
            )
            counts["bad_schema"] = 1
            return counts

        for rownum, row in enumerate(reader, start=2):
            counts["rows"] += 1
            enc = (row.get("encoding") or "").strip().lower()
            if enc not in AMO:
                # Baseline solvers or rows without a SAT encoding are not AMO CNFs.
                counts["ignored_non_amo"] += 1
                continue
            raw_vars = (row.get("nvars") or "").strip()
            raw_clauses = (row.get("nclauses") or "").strip()
            status = (row.get("status") or "").strip().upper()

            if not raw_vars or not raw_clauses:
                counts["missing_size"] += 1
                continue

            try:
                n = int(row["n"])
                got = (int(raw_vars), int(raw_clauses))
                sym = parse_sym(row.get("sym"), path, rownum)
                want = expected_size(n, enc, sym)
            except (TypeError, ValueError) as exc:
                print(f"ERROR {path}:{rownum}: {exc}", file=sys.stderr)
                counts["malformed"] += 1
                continue

            if got == (0, 0):
                if status in {"TO", "MO", "SKIP", "ERR", "ERROR",
                              "TIMEOUT", "MEMOUT"}:
                    counts["no_cnf"] += 1
                    continue
                print(
                    f"ERROR {path}:{rownum}: status={status!r} but CNF size is (0, 0)",
                    file=sys.stderr,
                )
                counts["malformed"] += 1
                continue

            if got[0] <= 0 or got[1] <= 0:
                print(
                    f"ERROR {path}:{rownum}: invalid partial CNF size {got}",
                    file=sys.stderr,
                )
                counts["malformed"] += 1
                continue

            counts["checked"] += 1
            if got != want:
                counts["mismatches"] += 1
                if counts["mismatches"] <= 5:
                    print(
                        f"MISMATCH {path.name}:{rownum}: N={n} enc={enc} sym={sym}; "
                        f"CSV={got}, formula={want}"
                    )

    print(
        f"{path.name:34s} rows={counts['rows']:3d} checked={counts['checked']:3d} "
        f"mismatch={counts['mismatches']:3d} missing_size={counts['missing_size']:3d} "
        f"no_CNF={counts['no_cnf']:3d} non_AMO={counts['ignored_non_amo']:3d} "
        f"malformed={counts['malformed']:3d}"
    )
    return counts


def closed_form_sanity_check() -> None:
    """Cross-check exact pairwise/seqcounter totals for N=1..100."""
    for n in range(1, 101):
        # Pairwise: 2N row/column lines, two diagonal families, plus 2N ALO.
        diag_pairwise = 2 * choose2(n) + 4 * (n * (n - 1) * (n - 2) // 6)
        pairwise_total = n * n * (n - 1) + diag_pairwise + 2 * n
        assert expected_size(n, "pairwise")[1] == pairwise_total
        if n >= 2:
            assert expected_size(n, "seqcounter") == (
                4 * n * n - 6 * n + 2 + n * n,
                12 * n * n - 22 * n + 12,
            )


def print_table() -> None:
    print("Predicted total CNF size (variables / clauses; no symmetry breaking):")
    for n in (100, 500, 1000, 2000):
        print(f"N={n}")
        for enc in AMO:
            variables, clauses = expected_size(n, enc)
            print(f"  {enc:10s} {variables:>12,d} {clauses:>15,d}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, default=ROOT / "results")
    parser.add_argument("--table", action="store_true", help="print predicted sizes")
    args = parser.parse_args()

    try:
        closed_form_sanity_check()
    except AssertionError:
        print("ERROR internal closed-form sanity check failed", file=sys.stderr)
        return 2

    print("Formula vs CSV (checking every recognized AMO row with recorded size):")
    totals = {
        "rows": 0, "checked": 0, "mismatches": 0, "ignored_non_amo": 0,
        "missing_size": 0, "no_cnf": 0, "malformed": 0,
        "missing_file": 0, "bad_schema": 0,
    }
    for filename in CSV_NAMES:
        counts = check_csv(args.results / filename)
        for key, val in counts.items():
            totals[key] = totals.get(key, 0) + val

    print(
        "TOTAL: "
        f"rows={totals['rows']} checked={totals['checked']} "
        f"mismatches={totals['mismatches']} missing_size={totals['missing_size']} "
        f"no_CNF={totals['no_cnf']} non_AMO={totals['ignored_non_amo']} "
        f"malformed={totals['malformed']} "
        f"missing_files={totals['missing_file']} bad_schema={totals['bad_schema']}"
    )
    if args.table:
        print()
        print_table()

    if any(totals.get(k, 0) for k in ("mismatches", "malformed", "missing_file", "bad_schema")):
        return 1
    if totals["checked"] == 0:
        print("ERROR no CNF rows were checked", file=sys.stderr)
        return 1
    print("PASS: all recorded, checkable AMO CNF sizes match the formulas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
