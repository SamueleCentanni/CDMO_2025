from itertools import combinations
from z3 import *
import time
import math
from utils import print_weekly_schedule


# ---- MANUAL TEST
from encoding_utils import exactly_one_totalizer, at_most_k_totalizer, heule_exactly_one, exactly_k_np, exactly_one_seq, exactly_one_bw, exactly_one_np, at_most_k_np, at_most_k_seq
from inutilities.opt_base import STS_Optimized_Model
from inutilities.opt_sb import STS_Optimized_Model_SB
from inutilities.opt_sb_encoding import STS_Optimized_Model_SB_Encodings
from inutilities.opt_sb_enc_solver import STS_Optimized_Model_SB_Solver
from inutilities.opt_sb_heule import STS_Optimized_Model_SB_Heule
from inutilities.opt_sb_optimizer import STS_Optimized_Model_SB_Heule_Optimize
from opt_sb_heule_3 import STS_Optimized_Model_SB_Heule_3
from inutilities.opt_sb_heule_2 import STS_Optimized_Model_SB_Heule_2

# ---- AUTOMATIC TEST
from solve import solve as solve_model


def main(n_teams, 
         exactly_one_encoding, 
         at_most_k_encoding,
         model_class, 
         timeout_seconds=5*60,
         verbose=True):
    
    if(verbose):
        print(f"Using exactly_one: {exactly_one_encoding.__name__}, and at_most_k: {at_most_k_encoding.__name__} and solver: {model_class.__name__}")
        print(f"Attempting to solve STS with Home/Away balance optimization for {n_teams} teams...")

    sts_model = model_class(n_teams, exactly_one_encoding, at_most_k_encoding)
    (objective, solution, optimality, solve_time, restarts, max_memory, mk_bool_var, conflicts) = sts_model.solve(timeout_seconds=timeout_seconds, random_seed=42)

    if verbose and solution:
        print(f"\nSchedule (n={n_teams}, Total Difference: {objective}):")
        print_weekly_schedule(solution, n_teams)
        print("\nFinal Stats:")
        print(f"  Optimality: {optimality}")
        print(f"  Solve Time: {solve_time:.2f}s")
        print(f"  Restarts: {restarts}, Conflicts: {conflicts}, Bool Vars: {mk_bool_var}, Max Memory: {max_memory:.2f} MB")

    # Ritorna tutto come richiesto
    return objective, solution, optimality, solve_time, restarts, max_memory, mk_bool_var, conflicts

    

if __name__ == '__main__':
    n_teams = 12
    
    
    ### BENCHMARK AUTOMATICO (solve)
    #'''
    results = solve_model(
        instance=n_teams,
        instance_number=1,
        timeout=300,
        random_seed=42,
    )

    for model_name, result in results.items():
        print(f"\n--- {model_name} ---")
        print(f"Objective: {result['obj']}")
        print(f"Optimal: {result['optimal']}")
        print(f"Time: {result['time']}s")
        print(f"Solution: {result['sol']}")
    
    
    '''
    ### TEST MANUALE     
    
    # STS_Optimized_Model
    # main(n_teams=n_teams, exactly_one_encoding=exactly_one_bw, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model)
    
    # STS_Optimized_Model_SB
    # main(n_teams=n_teams, exactly_one_encoding=exactly_one_bw, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB)

    # STS_Optimized_Model_SB_Encoding
    # main(n_teams=n_teams, exactly_one_encoding=exactly_one_seq, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB_Encodings)
    
    # main(n_teams=n_teams, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB_Solver)

    # main(n_teams=n_teams, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB_Heule)

    # main(n_teams=n_teams, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB_Heule_3)

    # main(n_teams=n_teams, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB_Heule_2)

    # main(n_teams=n_teams, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_totalizer, model_class=STS_Optimized_Model_SB_Heule_3)

    # grid_search(n_teams, at_most_k_encoding=at_most_k_totalizer)
    
    '''