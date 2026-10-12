import csv
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results" / "analysis"
OUT.mkdir(parents=True, exist_ok=True)


def number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def quantile(values, p):
    values = sorted(values)
    if not values:
        return None
    pos = (len(values) - 1) * p
    lo = int(pos)
    hi = min(lo + 1, len(values) - 1)
    return values[lo] + (values[hi] - values[lo]) * (pos - lo)


def fmt(value):
    return "" if value is None else f"{value:.6f}"


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    files = [Path(x) for x in sys.argv[1:]]
    if not files:
        raise SystemExit(
            "Usage: python3 experiments/analyze.py results/file1.csv ..."
        )

    groups = defaultdict(list)
    by_dataset_n_status = Counter()
    e1_rows = []
    total_rows = 0

    for path in files:
        if not path.is_file():
            raise SystemExit(f"Input file not found: {path}")

        with path.open(newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            fields = set(reader.fieldnames or [])

            # E1 records encoding size only; it has no solver column.
            if {"n", "encoding", "status", "nvars", "nclauses"} <= fields \
                    and "solver" not in fields:
                for row in reader:
                    total_rows += 1
                    dataset = path.name
                    n = (row.get("n") or "").strip()
                    encoding = (row.get("encoding") or "").strip()
                    status = (row.get("status") or "UNKNOWN").strip().upper()

                    by_dataset_n_status[(dataset, n, status)] += 1
                    e1_rows.append({
                        "dataset": dataset,
                        "n": n,
                        "encoding": encoding,
                        "status": status,
                        "nvars": (row.get("nvars") or "").strip(),
                        "nclauses": (row.get("nclauses") or "").strip(),
                    })
                continue

            required = {"n", "solver", "encoding", "status"}
            if not required.issubset(fields):
                raise SystemExit(
                    f"Unexpected CSV columns in {path}: {reader.fieldnames}"
                )

            for row in reader:
                total_rows += 1
                status = (row.get("status") or "UNKNOWN").strip().upper()
                if status == "TIMEOUT":
                    status = "TO"

                dataset = path.name
                n = (row.get("n") or "").strip()
                solver = (row.get("solver") or "").strip()
                encoding = (row.get("encoding") or "-").strip()
                sym = (row.get("sym") or "not_recorded").strip()

                by_dataset_n_status[(dataset, n, status)] += 1
                groups[(dataset, n, solver, encoding, sym)].append(row)

    # Encoding-size output, kept separate from solver timings.
    e1_fields = [
        "dataset", "n", "encoding", "status", "nvars", "nclauses"
    ]
    e1_rows.sort(key=lambda r: (int(r["n"]), r["encoding"]))
    write_csv(OUT / "encoding_size_summary.csv", e1_fields, e1_rows)

    # Runtime summary for datasets that have solver results.
    summary = []
    for (dataset, n, solver, encoding, sym), rows in sorted(
        groups.items(),
        key=lambda item: (
            item[0][0],
            int(item[0][1]) if item[0][1].isdigit() else -1,
            item[0][2], item[0][3], item[0][4],
        ),
    ):
        counts = Counter(
            "TO" if (r.get("status") or "").strip().upper() == "TIMEOUT"
            else (r.get("status") or "UNKNOWN").strip().upper()
            for r in rows
        )

        sat_rows = []
        for r in rows:
            if (r.get("status") or "").strip().upper() != "SAT":
                continue
            verification = (r.get("verify") or "").strip().lower()
            if verification in {"false", "0", "no"}:
                continue
            sat_rows.append(r)

        def med(field):
            values = [number(r.get(field)) for r in sat_rows]
            values = [v for v in values if v is not None]
            return statistics.median(values) if values else None

        times = [number(r.get("t_total")) for r in sat_rows]
        times = [v for v in times if v is not None]
        q1 = quantile(times, 0.25)
        q3 = quantile(times, 0.75)

        summary.append({
            "dataset": dataset,
            "n": n,
            "solver": solver,
            "encoding": encoding,
            "sym": sym,
            "runs_recorded": len(rows),
            "sat_status_runs": counts["SAT"],
            "sat_runs_used_for_medians": len(sat_rows),
            "to_runs": counts["TO"],
            "mo_runs": counts["MO"],
            "err_runs": counts["ERR"],
            "unsat_runs": counts["UNSAT"],
            "skip_runs": counts["SKIP"],
            "median_t_total_sat_s": fmt(med("t_total")),
            "q1_t_total_sat_s": fmt(q1),
            "q3_t_total_sat_s": fmt(q3),
            "iqr_t_total_sat_s": fmt(
                q3 - q1 if q1 is not None and q3 is not None else None
            ),
            "median_t_encode_sat_s": fmt(med("t_encode")),
            "median_t_solve_sat_s": fmt(med("t_solve")),
            "median_nvars_sat": fmt(med("nvars")),
            "median_nclauses_sat": fmt(med("nclauses")),
        })

    summary_fields = list(summary[0].keys()) if summary else [
        "dataset", "n", "solver", "encoding", "sym"
    ]
    write_csv(OUT / "solver_encoding_summary.csv", summary_fields, summary)

    status_rows = [
        {"dataset": d, "n": n, "status": s, "count": c}
        for (d, n, s), c in sorted(
            by_dataset_n_status.items(),
            key=lambda item: (
                item[0][0],
                int(item[0][1]) if item[0][1].isdigit() else -1,
                item[0][2],
            ),
        )
    ]
    write_csv(
        OUT / "status_counts.csv",
        ["dataset", "n", "status", "count"],
        status_rows,
    )

    report = [
        "# N-Queens benchmark analysis",
        "",
        f"- Input files: {len(files)}",
        f"- Total data records read: {total_rows}",
        "- Dataset summaries remain separate; Windows, VM and AWS runtimes "
        "must not be pooled into one ranking.",
        "- Runtime medians use SAT rows only; rows with an explicit false "
        "verification are excluded.",
        "- SKIP is counted separately and is not treated as an independent timeout.",
        "- t_total includes worker-process startup and other worker overhead.",
        "",
        "## Inputs",
    ]
    report += [f"- `{p}`" for p in files]
    report += [
        "",
        "## E1: CNF encoding sizes",
        "",
        "E1 measures the number of variables and clauses; it does not measure "
        "solver runtime.",
        "",
        "| N | Encoding | Status | Variables | Clauses |",
        "|---:|---|---|---:|---:|",
    ]
    for r in e1_rows:
        report.append(
            f"| {r['n']} | {r['encoding']} | {r['status']} | "
            f"{r['nvars']} | {r['nclauses']} |"
        )

    report += [
        "",
        "## Status totals by input file and N",
        "",
        "| Dataset | N | OK | SAT | TO | MO | ERR | UNSAT | SKIP |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    status_names = ("OK", "SAT", "TO", "MO", "ERR", "UNSAT", "SKIP")
    all_datasets = sorted({k[0] for k in by_dataset_n_status})
    for dataset in all_datasets:
        ns = sorted(
            {k[1] for k in by_dataset_n_status if k[0] == dataset},
            key=lambda x: int(x) if x.isdigit() else -1,
        )
        for n in ns:
            c = {
                s: by_dataset_n_status.get((dataset, n, s), 0)
                for s in status_names
            }
            report.append(
                f"| {dataset} | {n} | " +
                " | ".join(str(c[s]) for s in status_names) + " |"
            )

    (OUT / "analysis_report.md").write_text(
        "\n".join(report) + "\n", encoding="utf-8"
    )

    print(f"Read {total_rows} records from {len(files)} input files.")
    print(f"Encoding sizes: {OUT / 'encoding_size_summary.csv'}")
    print(f"Runtime summary: {OUT / 'solver_encoding_summary.csv'}")
    print(f"Statuses: {OUT / 'status_counts.csv'}")
    print(f"Report: {OUT / 'analysis_report.md'}")


if __name__ == "__main__":
    main()
