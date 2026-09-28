def verify(n, queens):
    if len(queens) != n:
        return False
    if any(not (0 <= c < n) for c in queens):
        return False
    if len(set(queens)) != n:
        return False
    if len({r - c for r, c in enumerate(queens)}) != n:
        return False
    if len({r + c for r, c in enumerate(queens)}) != n:
        return False
    return True
