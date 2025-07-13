from z3 import *

# --- Model Creation Function (adapted from the other group's `create_model`) ---
# This function will set up the core STS constraints and variables.
# It returns the solver, games_vars, home_counts, away_counts, diff_values, total_objective
# to be used in the solve method.
def create_sts_model(n, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=False, custom_solver=None):
    NUM_TEAMS = n
    NUM_WEEKS = NUM_TEAMS - 1
    NUM_PERIODS_PER_WEEK = n // 2
    
    if NUM_TEAMS % 2 != 0:
        raise ValueError(f"Error: The number of teams (n={NUM_TEAMS}) must be an even number.")

    solver_sts = Solver()
    # solver_sts = custom_solver if custom_solver is not None else Solver() # TORNA ALLA RIGA SOPRA SE OPTIMIZER NON FUNZION
    

    # --- Decision Variables ---
    games_vars = {}
    for i in range(NUM_TEAMS):
        for j in range(NUM_TEAMS):
            if i != j:
                for w in range(NUM_WEEKS):
                    for p in range(NUM_PERIODS_PER_WEEK):
                        games_vars[(i, j, w, p)] = Bool(f'g_{i+1}_{j+1}_{w+1}_{p+1}')
                        
    # --- Base Constraints ---
    # 1. Every pair plays exactly once (home or away)
    for i in range(NUM_TEAMS):
        for j in range(i+1, NUM_TEAMS):
            i_j_all_possible_matches = []
            for w in range(NUM_WEEKS):
                for p in range(NUM_PERIODS_PER_WEEK):
                    i_j_all_possible_matches.append(games_vars[(i, j, w, p)])
                    i_j_all_possible_matches.append(games_vars[(j, i, w, p)])
            solver_sts.add(exactly_one_encoding(i_j_all_possible_matches, f"pair_once_{i}_{j}"))
    
            
    # 2. Every team plays exactly once a week
    for i in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            once_week_game = []
            for j in range(NUM_TEAMS):
                if i == j: continue
                for p in range(NUM_PERIODS_PER_WEEK):
                    once_week_game.append(games_vars[(i,j,w,p)])
                    once_week_game.append(games_vars[(j,i,w,p)])
            solver_sts.add(exactly_one_encoding(once_week_game, f"team_once_week_{i}_{w}"))
            
    # 3. Every team plays at most twice in the same period over the tournament
    for i in range(NUM_TEAMS):
        for p in range(NUM_PERIODS_PER_WEEK):
            num_games_period = []
            for j in range(NUM_TEAMS):
                if i == j: continue
                for w in range(NUM_WEEKS):
                    num_games_period.append(games_vars[(i,j,w,p)])
                    num_games_period.append(games_vars[(j,i,w,p)])
            solver_sts.add(at_most_k_encoding(num_games_period, 2, f"team_at_most_2_period_{i}_{p}"))
            
    # 4. Exactly one game in each period of every week
    for w in range(NUM_WEEKS):
        for p in range(NUM_PERIODS_PER_WEEK):
            game_in_period = []
            for i in range(NUM_TEAMS):
                for j in range(i+1, NUM_TEAMS):
                    game_in_period.append(games_vars[(i,j,w,p)])
                    game_in_period.append(games_vars[(j,i,w,p)])
            solver_sts.add(exactly_one_encoding(game_in_period, f"slot_one_game_{w}_{p}"))
            
    # Symmetry Breaking 
    
    # 1. impose team that team one plays against team 2 in the first period during the first week
    if(symmetry_breaking):
        if NUM_TEAMS >= 2 and NUM_WEEKS >= 1 and NUM_PERIODS_PER_WEEK >= 1:
            solver_sts.add(games_vars[(0, 1, 0, 0)])

    # --- Optimization Variables ---
    home_counts = [Int(f'H_{i+1}') for i in range(NUM_TEAMS)]
    away_counts = [Int(f'A_{i+1}') for i in range(NUM_TEAMS)]
    diff_values = [Int(f'D_{i+1}') for i in range(NUM_TEAMS)] 

    # Constraints for home/away counts, using Z3's If and Sum for aggregation
    for i in range(NUM_TEAMS):
        home_games_for_team_i_bools = [games_vars[(i, j, w, p)] 
                                        for j in range(NUM_TEAMS) if i != j 
                                        for w in range(NUM_WEEKS) 
                                        for p in range(NUM_PERIODS_PER_WEEK)]
        solver_sts.add(home_counts[i] == Sum([If(v, 1, 0) for v in home_games_for_team_i_bools]))

        away_games_for_team_i_bools = [games_vars[(j, i, w, p)] 
                                        for j in range(NUM_TEAMS) if i != j 
                                        for w in range(NUM_WEEKS) 
                                        for p in range(NUM_PERIODS_PER_WEEK)]
        solver_sts.add(away_counts[i] == Sum([If(v, 1, 0) for v in away_games_for_team_i_bools]))

        solver_sts.add(home_counts[i] + away_counts[i] == NUM_WEEKS) 
        
        # Vincola diff_values[i] ad essere esattamente il valore assoluto
        solver_sts.add(diff_values[i] == If(home_counts[i] >= away_counts[i],
                                       home_counts[i] - away_counts[i],
                                       away_counts[i] - home_counts[i]))

    # Total difference (objective function)
    total_objective = Sum(diff_values)
    
    # --- ADDING THE LOWER BOUND CONSTRAINT HERE ---
    # Since n is always even, NUM_WEEKS (n-1) is always odd.
    # The minimum difference |H-A| for a single team is 1.
    # So, the sum of differences for all N_TEAMS is at least N_TEAMS * 1.
    lower_bound_total_diff = NUM_TEAMS 
    print(f"  Adding lower bound constraint: total_objective >= {lower_bound_total_diff}")
    solver_sts.add(total_objective >= lower_bound_total_diff)

    return solver_sts, games_vars, home_counts, away_counts, diff_values, total_objective