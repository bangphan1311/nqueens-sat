""" At most one

 in : lits, top 
 out  : (clauses, new top)

"""



def amo_pairwise(lits, top):
    clauses = []
    for i in range(len(lits)):
        for j in range(i + 1, len(lits)):
            clauses.append([-lits[i], -lits[j]])
    return clauses, top
