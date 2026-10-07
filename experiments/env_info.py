import datetime
import importlib.metadata as md
import os
import platform
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def pkg(name):
    try:
        return md.version(name)
    except Exception:
        return "n/a"


def cmd(c):
    try:
        r = subprocess.run(c, shell=True, capture_output=True, text=True, timeout=20)
        return r.stdout.strip()
    except Exception:
        return "n/a"


try:
    import gurobipy as gp
    gurobi = ".".join(map(str, gp.gurobi.version()))
except Exception:
    gurobi = "n/a"

kissat = cmd(os.path.expanduser("~/kissat/build/kissat") + " --version")
studio = cmd("ls ~/ibm/ILOG 2>/dev/null")
cpu = cmd("grep -m1 'model name' /proc/cpuinfo | cut -d: -f2")
cores = cmd("nproc")
mem_kb = int(cmd("awk '/MemTotal/ {print $2}' /proc/meminfo") or 0)
osname = cmd("grep PRETTY_NAME /etc/os-release | cut -d= -f2").strip('"')

lines = [
    "# Environment",
    "",
    f"Generated: {datetime.date.today()}",
    "",
    "## Machine",
    "",
    "| Item | Value |",
    "|---|---|",
    f"| OS | {osname} ({platform.machine()}) |",
    f"| CPU | {cpu} |",
    f"| Logical cores | {cores} |",
    f"| RAM | {mem_kb / 1024 / 1024:.1f} GiB |",
    "| Environment | virtual machine |",
    "",
    "## Software",
    "",
    "| Component | Version |",
    "|---|---|",
    f"| Python | {sys.version.split()[0]} |",
    f"| python-sat (PySAT) | {pkg('python-sat')} |",
    "| CaDiCaL | 1.5.3 (PySAT `cadical153`) |",
    "| Glucose | 4.x (PySAT `glucose4`) |",
    f"| Kissat | {kissat} (built from source, called via DIMACS) |",
    f"| CryptoMiniSat | pycryptosat {pkg('pycryptosat')} |",
    f"| OR-Tools (CP-SAT) | {pkg('ortools')} |",
    f"| Gurobi | {gurobi} (gurobipy {pkg('gurobipy')}) |",
    f"| CPLEX Studio | {studio} (python package cplex {pkg('cplex')}) |",
    f"| docplex | {pkg('docplex')} |",
    "",
]
out = os.path.join(HERE, "..", "results", "environment.md")
with open(out, "w") as f:
    f.write("\n".join(lines))
print("\n".join(lines))
