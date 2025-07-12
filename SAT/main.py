from itertools import combinations
from z3 import *
import time
import math
from utils import print_weekly_schedule

# ---- MANUAL TEST
from encoding_utils import heule_exactly_one, exactly_k_np, exactly_one_seq, exactly_one_bw, exactly_one_np, at_most_k_np, at_most_k_seq
from opt_base import STS_Optimized_Model
from opt_sb import STS_Optimized_Model_SB
from opt_sb_encoding import STS_Optimized_Model_SB_Encodings

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
    match_list, stats, final_model = sts_model.solve(timeout_seconds, random_seed=42)

    if match_list:
        print_weekly_schedule(match_list, n_teams)

        # Home/Away verification -> USELESS
        if(verbose):
            print("\nVerifying Home/Away balance for the final schedule:")
            for team_idx in range(n_teams):
                h_count = a_count = 0
                for (i, j, w, p) in match_list:
                    if i - 1 == team_idx:
                        h_count += 1
                    elif j - 1 == team_idx:
                        a_count += 1
                print(f"  Team {team_idx+1}: Home Games = {h_count}, Away Games = {a_count}, Difference = {abs(h_count - a_count)}")

if __name__ == '__main__':
    # main(n_teams=8, exactly_one_encoding=exactly_one_np, at_most_k_encoding=at_most_k_np, model_class=STS_Optimized_Model) -> TOO MUCH TIME 
    # main(n_teams=8, exactly_one_encoding=exactly_one_np, at_most_k_encoding=at_most_k_np, model_class=STS_Optimized_Model_SB) -> TOO MUCH TIME
    
    n_teams = 6
    
    ### DA USARE UNO DEI DUE TRA BENCHMARK AUTOMATICO OPPURE TEST MANUALE
    
    ### BENCHMARK AUTOMATICO (solve)
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
        # Aggiungi stampa calendario opzionalmente
    
    
    '''
    ### TEST MANUALE     
    # STS_Optimized_Model
    main(n_teams=n_teams, exactly_one_encoding=exactly_one_bw, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model)
    print("-------------------------------------------\n")
    # STS_Optimized_Model_SB
    main(n_teams=n_teams, exactly_one_encoding=exactly_one_bw, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB)
    print("-------------------------------------------\n")
    # STS_Optimized_Model_SB_Encoding
    main(n_teams=n_teams, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq, model_class=STS_Optimized_Model_SB_Encodings)
    '''
    