""" At most one

 in : lits, top 
 out  : (clauses, new top)

"""
from pysat.card import CardEnc, EncType


def amo_pairwise(lits, top):
    clauses = []
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            clauses.append([-lits[i], -lits[j]])
    return clauses, top


def amo_seqcounter(lits, top):
    n = len(lits)
    if n <= 1:                        
        return [], top
    
    s = [top + i + 1 for i in range(n - 1)]
    top = top + (n - 1)

    clauses = [[-lits[0], s[0]]]      # x1 -> s1
    for i in range(1, n - 1):
        clauses.append([-lits[i], s[i]])       # xi -> si
        clauses.append([-s[i - 1], s[i]])      # s(i-1) -> si
        clauses.append([-lits[i], -s[i - 1]])  # xi và s(i-1) không cùng đúng
    clauses.append([-lits[n - 1], -s[n - 2]])  
    return clauses, top

def _pysat_amo(lits, top, enc_type):
    """Ham dung chung: goi CardEnc.atmost cua PySAT voi 1 loai encoding."""
    cnf = CardEnc.atmost(lits=lits, bound=1, top_id=top, encoding=enc_type)
    new_top = max(top, cnf.nv)
    return cnf.clauses, new_top


def amo_bitwise(lits, top):
    return _pysat_amo(lits, top, EncType.bitwise)

def amo_commander(lits, top, group_size=3):
    if len(lits) <= 1:
        return [], top

    if len(lits) <= group_size:
        return amo_pairwise(lits, top)

    clauses = []
    commanders = []
    for i in range(0, len(lits), group_size):
        group = lits[i:i + group_size]
        if len(group) == 1:
            commanders.append(group[0])
            continue

        top += 1
        c = top  

        cl, top = amo_pairwise(group, top)
        clauses.extend(cl)
        for x in group:
            clauses.append([c, -x])  

        clauses.append([-c] + group) 
        commanders.append(c)

    cl, top = amo_commander(commanders, top, group_size)
    clauses.extend(cl)
    return clauses, top

def amo_product(lits, top):
    import math
    n = len(lits)
    if n <= 1:
        return [], top

    p = math.ceil(math.sqrt(n))   
    q = math.ceil(n / p)          

    row_vars = list(range(top + 1, top + 1 + p))
    top += p
    col_vars = list(range(top + 1, top + 1 + q))
    top += q

    clauses = []

    cl, top = amo_pairwise(row_vars, top)
    clauses.extend(cl)
    cl, top = amo_pairwise(col_vars, top)
    clauses.extend(cl)

    for i, x in enumerate(lits):
        r = i // q
        c = i % q
        clauses.append([-x, row_vars[r]])   
        clauses.append([-x, col_vars[c]])   

    return clauses, top
AMO_ENCODINGS = {
    "pairwise": amo_pairwise,
    "seqcounter": amo_seqcounter,
    "bitwise": amo_bitwise,
    "commander": amo_commander,
    "product": amo_product,
}
