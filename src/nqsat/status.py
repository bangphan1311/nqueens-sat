"""Common status codes. Wrappers may return older names; normalize() maps them."""
SAT, UNSAT, TO, MO, ERR = "SAT", "UNSAT", "TO", "MO", "ERR"

_MAP = {
    "SAT": SAT, "UNSAT": UNSAT,
    "TO": TO, "TIMEOUT": TO,
    "MO": MO, "MEMOUT": MO,
    "ERR": ERR, "ERROR": ERR,
}


def normalize(status):
    return _MAP.get(status, ERR)
