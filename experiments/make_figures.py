"""Draw the figures of the report from the raw result CSVs.

Reads only CSV files, never runs a solver. Medians use SAT rows only; whiskers are
min-max over the repetitions. A configuration whose repetition 0 ended in TO/MO is
drawn as a cross at the timeout line. SKIP rows are never drawn as measurements.

Usage:
  python experiments/make_figures.py [--results results] [--out figures]
Needs matplotlib. Every plotted number is also written to <out>/data_*.csv.
"""
import argparse
import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    raise SystemExit("matplotlib is required: install it in a separate environment, "
                     "not in the project .venv (it holds the patched CPLEX library).")

ROOT = Path(__file__).resolve().parents[1]
ENCODINGS = ["pairwise", "seqcounter", "bitwise", "commander", "product"]
SAT_SOLVERS = ["cadical", "glucose", "cryptominisat", "kissat"]
BASELINES = ["cpsat", "cpsat_bool", "gurobi", "cplex_mip", "cplex_cp"]
LABEL = {"cadical": "CaDiCaL", "glucose": "Glucose", "cryptominisat": "CryptoMiniSat",
         "kissat": "Kissat", "cpsat": "CP-SAT", "cpsat_bool": "CP-SAT (Boolean)",
         "gurobi": "Gurobi", "cplex_mip": "CPLEX MIP", "cplex_cp": "CPLEX CP"}
COLOR = {"cadical": "#1f77b4", "glucose": "#ff7f0e", "cryptominisat": "#2ca02c",
         "kissat": "#d62728", "cpsat": "#7f7f7f", "cpsat_bool": "#8c564b",
         "gurobi": "#9467bd", "cplex_mip": "#17becf", "cplex_cp": "#000000"}
MARK = {"cadical": "o", "glucose": "s", "cryptominisat": "^", "kissat": "D",
        "cpsat": "v", "cpsat_bool": "P", "gurobi": "X", "cplex_mip": "<", "cplex_cp": ">"}
ENC_COLOR = dict(zip(ENCODINGS, ["#d62728", "#1f77b4", "#2ca02c", "#ff7f0e", "#9467bd"]))
FAIL = {"TO": "TO", "TIMEOUT": "TO", "MO": "MO", "MEMOUT": "MO"}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read(path):
    if not path.is_file():
        print(f"  skip (missing): {path.name}")
        return None
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    print(f"  read {path.name}: {len(rows)} rows")
    return rows


def write_csv(path, fields, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def aggregate(rows, sym="0"):
    """-> {(solver, encoding, n): dict(med, lo, hi, n_sat, fail)}"""
    g = defaultdict(list)
    fails = {}
    for r in rows:
        if (r.get("sym") or "0").strip() != sym:
            continue
        key = (r["solver"], r["encoding"], int(r["n"]))
        st = (r.get("status") or "").strip().upper()
        t = num(r.get("t_total"))
        if st == "SAT" and t is not None:
            g[key].append(t)
        elif st in FAIL and int(r.get("rep") or 0) == 0:
            fails[key] = FAIL[st]
    out = {}
    for key in set(g) | set(fails):
        v = g.get(key, [])
        out[key] = dict(med=statistics.median(v) if v else None,
                        lo=min(v) if v else None, hi=max(v) if v else None,
                        n_sat=len(v), fail=fails.get(key))
    return out


def n_ticks(ax, ns):
    """Plain integer tick labels at the N values actually measured."""
    from matplotlib.ticker import NullFormatter, ScalarFormatter
    ns = sorted(set(ns))
    ax.set_xticks(ns)
    ax.xaxis.set_major_formatter(ScalarFormatter())
    ax.xaxis.set_minor_formatter(NullFormatter())


def save(fig, out, name):
    for ext in ("png", "pdf"):
        fig.savefig(out / f"{name}.{ext}", dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {name}.png / .pdf")


def fig_e1(rows, out):
    d = defaultdict(dict)
    for r in rows:
        nv, nc = num(r.get("nvars")), num(r.get("nclauses"))
        if nv is not None and nc is not None and r["encoding"] in ENCODINGS:
            d[r["encoding"]][int(r["n"])] = (nv, nc)
    fig, ax = plt.subplots(1, 2, figsize=(10, 4))
    data = []
    for enc in ENCODINGS:
        ns = sorted(d[enc])
        if not ns:
            continue
        for k, title in ((0, "Variables"), (1, "Clauses")):
            ax[k].plot(ns, [d[enc][n][k] for n in ns], marker="o", ms=4,
                       color=ENC_COLOR[enc], label=enc)
            ax[k].set_title(title)
        data += [dict(encoding=enc, n=n, nvars=int(d[enc][n][0]), nclauses=int(d[enc][n][1])) for n in ns]
    allns = [n for enc in ENCODINGS for n in d[enc]]
    for a in ax:
        a.set_xscale("log"); a.set_yscale("log"); a.set_xlabel("N"); a.grid(alpha=.3, which="both")
        n_ticks(a, allns)
    ax[0].legend(fontsize=8)
    fig.suptitle("E1: CNF size by encoding", y=1.02)
    write_csv(out / "data_e1.csv", ["encoding", "n", "nvars", "nclauses"], data)
    save(fig, out, "fig_e1_sizes")


def fig_e2(rows, out):
    agg = aggregate(rows)
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    data = []
    for enc in ENCODINGS:
        pts = sorted((k[2], v) for k, v in agg.items() if k[1] == enc and v["med"] is not None)
        if not pts:
            continue
        ns = [p[0] for p in pts]
        med = [p[1]["med"] for p in pts]
        err = [[m - p[1]["lo"] for m, p in zip(med, pts)], [p[1]["hi"] - m for m, p in zip(med, pts)]]
        ax.errorbar(ns, med, yerr=err, marker="o", ms=4, capsize=2, color=ENC_COLOR[enc], label=enc)
        data += [dict(encoding=enc, n=n, median_s=round(v["med"], 4), min_s=round(v["lo"], 4),
                      max_s=round(v["hi"], 4), sat_runs=v["n_sat"]) for n, v in pts]
    ax.set_yscale("log"); ax.set_xscale("log"); ax.set_xlabel("N"); ax.set_ylabel("median t_total (s)")
    n_ticks(ax, [d["n"] for d in data])
    ax.set_title("E2: AMO encodings with Glucose (Linux VM)\nwhiskers = min-max over repetitions")
    ax.grid(alpha=.3, which="both"); ax.legend(fontsize=8)
    write_csv(out / "data_e2.csv", ["encoding", "n", "median_s", "min_s", "max_s", "sat_runs"], data)
    save(fig, out, "fig_e2_encodings_glucose")


def draw_lines(ax, agg, solver, enc, timeout, dashed):
    pts = sorted((k[2], v) for k, v in agg.items() if k[0] == solver and k[1] == enc)
    ok = [(n, v) for n, v in pts if v["med"] is not None]
    st = dict(color=COLOR[solver], marker=MARK[solver], ms=5, lw=1.4,
              ls="--" if dashed else "-", label=LABEL[solver])
    if ok:
        ax.plot([n for n, _ in ok], [v["med"] for _, v in ok], **st)
    else:
        ax.plot([], [], **st)
    for n, v in pts:
        if v["fail"]:
            ax.plot([n], [timeout], marker="x", color=COLOR[solver], ms=9, mew=2, ls="none")
    return [dict(solver=solver, encoding=enc, n=n, median_s=None if v["med"] is None else round(v["med"], 4),
                 sat_runs=v["n_sat"], rep0_failure=v["fail"] or "") for n, v in pts]


def fig_e4(rows, out, timeout):
    agg = aggregate(rows)
    encs = [e for e in ("commander", "product") if any(k[1] == e for k in agg)]
    fig, axes = plt.subplots(1, len(encs), figsize=(5.6 * len(encs), 4.6), sharey=True, squeeze=False)
    data = []
    for ax, enc in zip(axes[0], encs):
        for s in SAT_SOLVERS:
            data += draw_lines(ax, agg, s, enc, timeout, dashed=False)
        for s in BASELINES:
            data += draw_lines(ax, agg, s, "-", timeout, dashed=True)
        ax.axhline(timeout, color="k", lw=.8, ls=":")
        ax.set_yscale("log"); ax.set_xscale("log"); ax.set_xlabel("N"); ax.grid(alpha=.3, which="both")
        n_ticks(ax, [k[2] for k in agg])
        ax.set_title(f"SAT solvers with {enc} encoding (dashed = baselines)", fontsize=10)
    axes[0][0].set_ylabel("median t_total (s)")
    h, l = axes[0][-1].get_legend_handles_labels()
    fig.legend(h, l, loc="center left", bbox_to_anchor=(1.0, .5), fontsize=8, title="solver")
    fig.suptitle(f"E4: solver comparison on the Linux VM. Cross = timeout or memory-out at "
                 f"repetition 0; dotted line = {timeout:g} s", fontsize=10, y=1.02)
    write_csv(out / "data_e4.csv", ["solver", "encoding", "n", "median_s", "sat_runs", "rep0_failure"], data)
    save(fig, out, "fig_e4_solvers")


def fig_e5(nosym, sym, out):
    a0, a1 = aggregate(nosym, "0"), aggregate(sym, "1")
    keys = sorted(a0, key=lambda k: (k[0], k[2]))
    keys = [k for k in keys if a0[k]["med"] is not None and k in a1 and a1[k]["med"] is not None]
    if not keys:
        print("  skip E5: no matching rows")
        return
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    w, data = .38, []
    for i, k in enumerate(keys):
        m0, m1 = a0[k]["med"], a1[k]["med"]
        ax.bar(i - w / 2, m0, w, color="#9ecae1", label="no symmetry breaking" if i == 0 else None)
        ax.bar(i + w / 2, m1, w, color="#3182bd", label="symmetry breaking" if i == 0 else None)
        pct = 100 * (m1 - m0) / m0
        ax.text(i + w / 2, m1, f"{pct:+.0f}%", ha="center", va="bottom", fontsize=8)
        data.append(dict(solver=k[0], encoding=k[1], n=k[2], median_nosym_s=round(m0, 4),
                         median_sym_s=round(m1, 4), change_percent=round(pct, 1)))
    ax.set_xticks(range(len(keys)))
    ax.set_xticklabels([f"{LABEL[k[0]]}\nN={k[2]}" for k in keys], fontsize=8)
    ax.set_ylabel("median t_total (s)"); ax.legend(fontsize=8); ax.grid(alpha=.3, axis="y")
    ax.set_title("E5: symmetry breaking (commander encoding)")
    write_csv(out / "data_e5.csv", ["solver", "encoding", "n", "median_nosym_s", "median_sym_s", "change_percent"], data)
    save(fig, out, "fig_e5_symmetry")


def fig_large(rows, out, timeout):
    agg = aggregate(rows)
    ns = sorted({k[2] for k in agg})
    if not ns:
        return
    fig, axes = plt.subplots(1, len(ns), figsize=(6.4 * len(ns), 4.8), squeeze=False, layout="constrained")
    data = []
    for ax, n in zip(axes[0], ns):
        items = sorted(((k, v) for k, v in agg.items() if k[2] == n),
                       key=lambda kv: (kv[1]["med"] is None, kv[1]["med"] or timeout))
        for i, (k, v) in enumerate(items):
            name = LABEL[k[0]] + ("" if k[1] == "-" else f" + {k[1]}")
            if v["med"] is not None:
                err = [[v["med"] - v["lo"]], [v["hi"] - v["med"]]]
                ax.barh(i, v["med"], xerr=err, color=COLOR[k[0]], error_kw=dict(lw=1, capsize=2))
            else:
                ax.barh(i, timeout, color="none", edgecolor=COLOR[k[0]], hatch="//")
                ax.text(timeout * 1.15, i, v["fail"] or "no SAT run", va="center", fontsize=8)
            data.append(dict(n=n, solver=k[0], encoding=k[1],
                             median_s=None if v["med"] is None else round(v["med"], 3),
                             sat_runs=v["n_sat"], rep0_failure=v["fail"] or ""))
        ax.set_yticks(range(len(items)))
        ax.set_yticklabels([LABEL[k[0]] + ("" if k[1] == "-" else f" + {k[1]}") for k, _ in items], fontsize=8)
        ax.invert_yaxis(); ax.set_xscale("log"); ax.set_xlabel("median t_total (s)")
        meds = [v["med"] for _, v in items if v["med"] is not None]
        ax.set_xlim(left=(min(meds) / 1.8) if meds else 1, right=timeout * 2.2)
        ax.set_title(f"N = {n}"); ax.grid(alpha=.3, axis="x", which="both")
    fig.suptitle("Large N on AWS. Hatched = timeout or memory-out at repetition 0", fontsize=10)
    write_csv(out / "data_large.csv", ["n", "solver", "encoding", "median_s", "sat_runs", "rep0_failure"], data)
    save(fig, out, "fig_large_n_aws")


def fig_status(datasets, out):
    order = ["SAT", "UNSAT", "TO", "MO", "ERR", "SKIP"]
    col = {"SAT": "#2ca02c", "UNSAT": "#98df8a", "TO": "#ff7f0e", "MO": "#d62728",
           "ERR": "#000000", "SKIP": "#bbbbbb"}
    names, counts = [], []
    for name, rows in datasets:
        c = defaultdict(int)
        for r in rows:
            st = (r.get("status") or "").strip().upper()
            c[FAIL.get(st, st)] += 1
        names.append(name); counts.append(c)
    fig, ax = plt.subplots(figsize=(8, 0.6 * len(names) + 1.8))
    left = [0] * len(names)
    for st in order:
        vals = [c.get(st, 0) for c in counts]
        if any(vals):
            ax.barh(range(len(names)), vals, left=left, color=col[st], label=st)
            left = [a + b for a, b in zip(left, vals)]
    ax.set_yticks(range(len(names))); ax.set_yticklabels(names, fontsize=8); ax.invert_yaxis()
    ax.set_xlabel("number of runs"); ax.legend(fontsize=8, ncol=6, loc="lower center", bbox_to_anchor=(.5, 1.0))
    write_csv(out / "data_status.csv", ["dataset"] + order,
              [dict(dataset=n, **{s: c.get(s, 0) for s in order}) for n, c in zip(names, counts)])
    save(fig, out, "fig_status_counts")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default=str(ROOT / "results"))
    ap.add_argument("--out", default=str(ROOT / "figures"))
    ap.add_argument("--timeout", type=float, default=300, help="timeout line drawn in the plots")
    a = ap.parse_args()
    res, out = Path(a.results), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    print("Reading:")
    e1, e2 = read(res / "e1_sizes.csv"), read(res / "e2_encoding_glucose.csv")
    e4, e5n, e5s = read(res / "e4_vm.csv"), read(res / "e5_nosym.csv"), read(res / "e5_sym.csv")
    big = read(res / "large_commander_product.csv")

    print("Drawing:")
    if e1: fig_e1(e1, out)
    if e2: fig_e2(e2, out)
    if e4: fig_e4(e4, out, a.timeout)
    if e5n and e5s: fig_e5(e5n, e5s, out)
    if big: fig_large(big, out, a.timeout)
    sets = [(n, r) for n, r in (("E2 Linux VM", e2), ("E4 Linux VM", e4), ("E5 no sym", e5n),
                                ("E5 sym", e5s), ("AWS large N", big)) if r]
    if sets: fig_status(sets, out)
    print(f"Done. Figures and data_*.csv are in {out}")


if __name__ == "__main__":
    main()
