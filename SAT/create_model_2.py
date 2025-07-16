from z3 import *

def create_sts_model_compact(n, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=False, custom_solver=None):
    """
        different variables definition: 
            match_vars[i,j,w,p]: team i plays against team j on week w in period p, for each i < j
                In this way, the number of variables wrt 'create_model' is halved
            home_vars[i,j]: team i plays at home against team j
            game_vars[i,j,w,p]: variables which relate match_vars and home_vars -> 
                                team i plays at home against team j on week w on period p
                                I need these variables to derive home_counts and away_counts 
        constraints definition
        objective value definition: minimize the sum of the absolute differences between home and away matches
            for each team
    """
    
    NUM_TEAMS = n
    NUM_WEEKS = NUM_TEAMS - 1
    NUM_PERIODS_PER_WEEK = n // 2
    
    if NUM_TEAMS % 2 != 0:
        raise ValueError(f"Error: The number of teams (n={NUM_TEAMS}) must be even.")
    
    solver_sts = Solver() if custom_solver is None else custom_solver
    
    # --- Decision Variables ---
    
    # i plays against j 
    match_vars = {}
    for i in range(NUM_TEAMS):
        for j in range(i+1, NUM_TEAMS):
            for w in range(NUM_WEEKS):
                for p in range(NUM_PERIODS_PER_WEEK):
                    match_vars[(i,j,w,p)] = Bool(f'm_{i+1}_{j+1}_{w+1}_{p+1}')
    
    # i plays at home against j
    home_vars = {}
    for i in range(NUM_TEAMS):
        for j in range(i+1, NUM_TEAMS):
            home_vars[(i,j)] = Bool(f'home_{i+1}_{j+1}')
    
    # --- Base Constraints ---
    # 1. Every pair plays exactly once (home or away)
    for i in range(NUM_TEAMS):
        for j in range(i+1, NUM_TEAMS):
            all_slots = [match_vars[(i,j,w,p)] for w in range(NUM_WEEKS) for p in range(NUM_PERIODS_PER_WEEK)]
            solver_sts.add(exactly_one_encoding(all_slots, f"pair_once_{i}_{j}"))
    
    # 2. Every team plays exactly once a week
    for t in range(NUM_TEAMS):
        for w in range(NUM_WEEKS):
            matches_this_week = []
            for i in range(NUM_TEAMS):
                for j in range(i+1, NUM_TEAMS):
                    if t == i or t == j:
                        for p in range(NUM_PERIODS_PER_WEEK):
                            matches_this_week.append(match_vars[(i,j,w,p)])
            solver_sts.add(exactly_one_encoding(matches_this_week, f"team_once_week_{t}_{w}"))
    
    # 3. Every team plays at most twice in the same period over the tournament
    for t in range(NUM_TEAMS):
        for p in range(NUM_PERIODS_PER_WEEK):
            matches_in_period = []
            for i in range(NUM_TEAMS):
                for j in range(i+1, NUM_TEAMS):
                    if t == i or t == j:
                        for w in range(NUM_WEEKS):
                            matches_in_period.append(match_vars[(i,j,w,p)])
            solver_sts.add(at_most_k_encoding(matches_in_period, 2, f"team_at_most_2_period_{t}_{p}"))
    
    # 4. Exactly one game in each period of every week
    for w in range(NUM_WEEKS):
        for p in range(NUM_PERIODS_PER_WEEK):
            matches_in_slot = [match_vars[(i,j,w,p)] for i in range(NUM_TEAMS) for j in range(i+1, NUM_TEAMS)]
            solver_sts.add(exactly_one_encoding(matches_in_slot, f"slot_one_game_{w}_{p}"))
    
    # Linking match_vars and home_vars 
    games_vars = {}
    for i in range(NUM_TEAMS):
        for j in range(NUM_TEAMS):
            if i == j:
                continue
            if i < j:
                for w in range(NUM_WEEKS):
                    for p in range(NUM_PERIODS_PER_WEEK):
                        var_name = f'g_{i+1}_{j+1}_{w+1}_{p+1}'
                        games_vars[(i,j,w,p)] = Bool(var_name)
                        solver_sts.add(games_vars[(i,j,w,p)] == And(match_vars[(i,j,w,p)], home_vars[(i,j)]))
            else:
                for w in range(NUM_WEEKS):
                    for p in range(NUM_PERIODS_PER_WEEK):
                        var_name = f'g_{i+1}_{j+1}_{w+1}_{p+1}'
                        games_vars[(i,j,w,p)] = Bool(var_name)
                        solver_sts.add(games_vars[(i,j,w,p)] == And(match_vars[(j,i,w,p)], Not(home_vars[(j,i)])))
    
    # --- Optimization Variables ---
    home_counts = [Int(f'H_{i+1}') for i in range(NUM_TEAMS)]
    away_counts = [Int(f'A_{i+1}') for i in range(NUM_TEAMS)]
    diff_values = [Int(f'D_{i+1}') for i in range(NUM_TEAMS)]
    
    for i in range(NUM_TEAMS):
        home_games = [games_vars[(i,j,w,p)] 
                      for j in range(NUM_TEAMS) if i != j 
                      for w in range(NUM_WEEKS) 
                      for p in range(NUM_PERIODS_PER_WEEK)]
        solver_sts.add(home_counts[i] == Sum([If(v, 1, 0) for v in home_games]))
        
        away_games = [games_vars[(j,i,w,p)] 
                      for j in range(NUM_TEAMS) if i != j 
                      for w in range(NUM_WEEKS) 
                      for p in range(NUM_PERIODS_PER_WEEK)]
        solver_sts.add(away_counts[i] == Sum([If(v, 1, 0) for v in away_games]))
        
        solver_sts.add(home_counts[i] + away_counts[i] == NUM_WEEKS)
        
        solver_sts.add(diff_values[i] == If(home_counts[i] >= away_counts[i], 
                                            home_counts[i] - away_counts[i], 
                                            away_counts[i] - home_counts[i]))
    
    # objective function
    total_objective = Sum(diff_values)
    
    # --- LOWER BOUND CONSTRAINT ---
    # Since n is always even, NUM_WEEKS (n-1) is always odd.
    # The minimum difference |H-A| for a single team is 1.
    # So, the sum of differences for all N_TEAMS is at least N_TEAMS * 1.
    solver_sts.add(total_objective >= NUM_TEAMS)  
    
    # --- Symmetry Breaking ---
    # 1. impose team that team one plays against team 2 in the first period during the first week
    if symmetry_breaking:
        solver_sts.add(games_vars[(0, 1, 0, 0)])
    
    return solver_sts, games_vars, home_counts, away_counts, diff_values, total_objective