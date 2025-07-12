from itertools import combinations
from z3 import *
import math

# Naive/Pairwise (NP)
def at_least_one_np(bool_vars):
    if not bool_vars: return BoolVal(False)
    return Or(bool_vars)

def at_most_one_np(bool_vars):
    if len(bool_vars) < 2: return []
    return [Not(And(bool_vars[i], bool_vars[j])) for i in range(len(bool_vars) - 1) for j in range(i+1, len(bool_vars))]

def exactly_one_np(bool_vars, name=''):
    return And(*at_most_one_np(bool_vars), at_least_one_np(bool_vars))
#--------------------------------------------------------------------------------------------------------------------------------------------------------

# Binary Encoding (BW)
def toBinary(num, length = None):
    num_bin = bin(num).split("b")[-1]
    if length:
        return "0"*(length - len(num_bin)) + num_bin
    return num_bin
    
def at_least_one_bw(bool_vars):
    return at_least_one_np(bool_vars)

def at_most_one_bw(bool_vars, name=''):
    constraints = []
    n = len(bool_vars)
    if n == 0: return BoolVal(True)
    
    m = math.ceil(math.log2(n))
    r = [Bool(f"r_{name}_{i}") for i in range(m)]
    binaries = [toBinary(idx, m) for idx in range(n)]
    
    for i in range(n):
        phi_parts = []
        for j in range(m):
            if binaries[i][j] == "1":
                phi_parts.append(r[j])
            else:
                phi_parts.append(Not(r[j]))
        constraints.append(Or(Not(bool_vars[i]), And(*phi_parts)))

    return And(constraints)

def exactly_one_bw(bool_vars, name=''):
    return And(at_least_one_bw(bool_vars), at_most_one_bw(bool_vars, name))
#--------------------------------------------------------------------------------------------------------------------------------------------------------

# Sequential Encoding (SEQ for k=1)
def at_least_one_seq(bool_vars):
    return at_least_one_np(bool_vars)

def at_most_one_seq(bool_vars, name=''):
    constraints = []
    n = len(bool_vars)
    if n == 0: return BoolVal(True)
    if n == 1: return BoolVal(True) 

    s = [Bool(f"s_{name}_{i}") for i in range(n - 1)]

    constraints.append(Or(Not(bool_vars[0]), s[0]))
    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2])))
    
    for i in range(1, n - 1):
        constraints.append(Or(Not(bool_vars[i]), s[i]))
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1])))
        constraints.append(Or(Not(s[i-1]), s[i]))
    
    return And(constraints)

def exactly_one_seq(bool_vars, name=''):
    return And(at_least_one_seq(bool_vars), at_most_one_seq(bool_vars, name))
#--------------------------------------------------------------------------------------------------------------------------------------------------------

# General K-Encoding (NP - Direct Encoding)
def at_least_k_np(bool_vars, k, name = ""):
    return at_most_k_np([Not(var) for var in bool_vars], len(bool_vars)-k, name)

def at_most_k_np(bool_vars, k, name = ""):
    if k >= len(bool_vars): return BoolVal(True) 
    if k < 0: return BoolVal(False)
    return And([Or([Not(x) for x in X]) for X in combinations(bool_vars, k + 1)])

def exactly_k_np(bool_vars, k, name = ""):
    return And(at_most_k_np(bool_vars, k, name), at_least_k_np(bool_vars, k, name))


# General K-Encoding (SEQ - Sequential Counter Encoding)
def at_most_k_seq(bool_vars, k, name=''):
    constraints = []
    n = len(bool_vars)
    
    if n == 0: return BoolVal(True)
    if k == 0: return And([Not(v) for v in bool_vars])
    if k >= n: return BoolVal(True)

    s = [[Bool(f"s_{name}_{i}_{j}") for j in range(k)] for i in range(n)] 
    
    constraints.append(Or(Not(bool_vars[0]), s[0][0])) 
    for j in range(1, k):
        constraints.append(Not(s[0][j]))

    for i in range(1, n):
        constraints.append(Or(Not(s[i-1][0]), s[i][0]))
        constraints.append(Or(Not(bool_vars[i]), s[i][0]))

        for j in range(1, k):
            constraints.append(Or(Not(s[i-1][j]), s[i][j]))
            constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][j-1]), s[i][j]))
        
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][k-1])))

    return And(constraints)

def at_least_k_seq(bool_vars, k, name=''):
    return at_most_k_seq([Not(var) for var in bool_vars], len(bool_vars)-k, name + "_neg")

def exactly_k_seq(bool_vars, k, name=''):
    return And(at_most_k_seq(bool_vars, k, name), at_least_k_seq(bool_vars, k, name))
#--------------------------------------------------------------------------------------------------------------------------------------------------------

# --- Heule Encoding Approach (from the other group's code) ---
# This will be used specifically for exactly_one in the STS problem.
# The original `at_most_one_he` in your code was different.
global_most_counter = 0 # Renamed to avoid conflict with potential local vars

def heule_at_most_one(bool_vars):
    # This is the recursive Heule AMO used by the other group
    if len(bool_vars) <= 4: # Base case: use pairwise encoding
        return And([Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)])
    else:
        global global_most_counter
        global_most_counter += 1
        aux_var = Bool(f'y_amo_{global_most_counter}') # Using a distinct name for auxiliary vars

        # This recursive decomposition is the core of their Heule encoding
        # It splits into roughly 1/4 and 3/4, with an auxiliary variable
        return And(heule_at_most_one(bool_vars[:3] + [aux_var]), heule_at_most_one([Not(aux_var)] + bool_vars[3:]))

def heule_exactly_one(bool_vars, name=''):
    # Uses the Heule AMO and the simple at_least_one
    return And(heule_at_most_one(bool_vars), at_least_one_np(bool_vars)) # Using your at_least_one_np