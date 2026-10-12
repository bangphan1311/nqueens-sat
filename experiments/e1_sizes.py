import csv
import gc
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from nqsat import amo
from nqsat.encode import build_cnf

ENCODINGS = [
    ("pairwise", amo.amo_pairwise),
    ("seqcounter", amo.amo_seqcounter),
    ("bitwise", amo.amo_bitwise),
    ("commander", amo.amo_commander),
    ("product", amo.amo_product),
]

NS = [4, 8, 16, 32, 50, 64, 80, 100]
OUTPUT = ROOT / "results" / "e1_sizes.csv"


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = ["n", "encoding", "sym", "status", "nvars", "nclauses", "error"]

    with OUTPUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        f.flush()

        for n in NS:
            for name, encoder in ENCODINGS:
                print(f"Building N={n}, encoding={name}...", flush=True)
                clauses = None

                try:
                    clauses, top = build_cnf(n, encoder, sym=False)
                    row = {
                        "n": n,
                        "encoding": name,
                        "sym": False,
                        "status": "OK",
                        "nvars": top,
                        "nclauses": len(clauses),
                        "error": "",
                    }
                except MemoryError:
                    row = {
                        "n": n,
                        "encoding": name,
                        "sym": False,
                        "status": "MO",
                        "nvars": "",
                        "nclauses": "",
                        "error": "MemoryError",
                    }
                except Exception as exc:
                    row = {
                        "n": n,
                        "encoding": name,
                        "sym": False,
                        "status": "ERR",
                        "nvars": "",
                        "nclauses": "",
                        "error": repr(exc)[:200],
                    }

                writer.writerow(row)
                f.flush()
                print(
                    f"  status={row['status']}, "
                    f"vars={row['nvars']}, clauses={row['nclauses']}",
                    flush=True,
                )

                del clauses
                gc.collect()

    print(f"\nResults saved to: {OUTPUT}")


if __name__ == "__main__":
    main()
