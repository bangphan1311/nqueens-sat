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

AMO_ENCODINGS = {
    "pairwise": amo_pairwise,
    "seqcounter": amo_seqcounter,
    "binary": amo_bitwise,
}
