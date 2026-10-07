def var(n, r, c):
    return r * n + c + 1


def build_cnf(n, amo, sym=False):
    clauses = []
    top = n * n

    def add_amo(lits):
        nonlocal top
        cl, top = amo(lits, top)
        clauses.extend(cl)

    for r in range(n):
        lits = [var(n, r, c) for c in range(n)]
        clauses.append(lits[:])
        add_amo(lits)

    for c in range(n):
        lits = [var(n, r, c) for r in range(n)]
        clauses.append(lits[:])
        add_amo(lits)

    for d in range(-(n - 1), n):
        lits = [var(n, r, r - d) for r in range(n) if 0 <= r - d < n]
        add_amo(lits)

    for s in range(0, 2 * n - 1):
        lits = [var(n, r, s - r) for r in range(n) if 0 <= s - r < n]
        add_amo(lits)

    if sym:
        # vertical-reflection symmetry breaking: row-0 queen in the left half
        # (including the middle column when n is odd)
        for c in range((n - 1) // 2 + 1, n):
            clauses.append([-var(n, 0, c)])

    return clauses, top


def decode(n, model):
    true_vars = {v for v in model if v > 0}
    queens = []
    for r in range(n):
        for c in range(n):
            if var(n, r, c) in true_vars:
                queens.append(c)
                break
    return queens
