from z3 import *

def create_sts_model_compact_optimized(n, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=False, custom_solver=None):
    '''
        different variables definition: 
            match_vars[i,j,w,p]: team i plays against team j on week w in period p, for each i < j
                In this way, the number of variables wrt 'create_model' is halved
            home_vars[i,j]: team i plays at home against team j
            Now, i can directly derive the home_counts and away_counts  
        constraints definition
        objective value definition: minimize the sum of the absolute differences between home and away matches
            for each team
    '''
    
    
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
    
    # --- Optimization Variables ---
    home_counts = [Int(f'H_{i+1}') for i in range(NUM_TEAMS)]
    away_counts = [Int(f'A_{i+1}') for i in range(NUM_TEAMS)]
    diff_values = [Int(f'D_{i+1}') for i in range(NUM_TEAMS)]
    
    # direct derivation of home_counts and away_counts
    for team_idx in range(NUM_TEAMS):
        current_team_home_games_expressions = []
        current_team_away_games_expressions = []

        for opp_idx in range(NUM_TEAMS):
            if team_idx == opp_idx:
                continue

            for w in range(NUM_WEEKS):
                for p in range(NUM_PERIODS_PER_WEEK):
                    if team_idx < opp_idx: 
                        match_var = match_vars[(team_idx, opp_idx, w, p)] # boolean values
                        h_var_pair = home_vars[(team_idx, opp_idx)] # boolean values
                        
                        # If match_var is True and h_var_pair is True -> team_idx plays at home
                        current_team_home_games_expressions.append(And(match_var, h_var_pair))
                        # If match_var is True and h_var_pair is False -> team_idx plays away
                        current_team_away_games_expressions.append(And(match_var, Not(h_var_pair)))

                    else: 
                        match_var = match_vars[(opp_idx, team_idx, w, p)]
                        h_var_pair = home_vars[(opp_idx, team_idx)]
                        
                        # If match_var is True and h_var_pair is False -> team_idx plays at home
                        current_team_home_games_expressions.append(And(match_var, Not(h_var_pair)))
                        # If match_var is True and h_var_pair is True -> team_idx plays away
                        current_team_away_games_expressions.append(And(match_var, h_var_pair))

        
        solver_sts.add(home_counts[team_idx] == Sum([If(v, 1, 0) 
                                                     for v in current_team_home_games_expressions]))
        solver_sts.add(away_counts[team_idx] == Sum([If(v, 1, 0) 
                                                     for v in current_team_away_games_expressions]))
        
        solver_sts.add(home_counts[team_idx] + away_counts[team_idx] == NUM_WEEKS)
        
        solver_sts.add(diff_values[team_idx] == If(home_counts[team_idx] >= away_counts[team_idx],
                                       home_counts[team_idx] - away_counts[team_idx],
                                       away_counts[team_idx] - home_counts[team_idx]))
    
    # objective function
    total_objective = Sum(diff_values)
    
    # --- LOWER BOUND CONSTRAINT ---
    # Since n is always even, NUM_WEEKS (n-1) is always odd.
    # The minimum difference |H-A| for a single team is 1.
    # So, the sum of differences for all N_TEAMS is at least N_TEAMS * 1.
    lower_bound = NUM_TEAMS
    solver_sts.add(total_objective >= lower_bound)
    
    
    # Symmetry breaking 
    if symmetry_breaking:
        # Forza la prima partita: team 0 in casa contro team 1 nella prima settimana e periodo
        # Questo implica match_vars[(0,1,0,0)] e home_vars[(0,1)]
        #solver_sts.add(match_vars[(0, 1, 0, 0)]) # La partita tra 0 e 1 si gioca nella W1, P1
        #solver_sts.add(home_vars[(0, 1)])       # E il team 0 gioca in casa

    
        # since NUM_TEAMS can be big, instead of fixing only the first game 
        # i fix all the games of the first team
        for w in range(NUM_WEEKS):
            opponent_for_team0 = w + 1

            team_a, team_b = (0, opponent_for_team0) if 0 < opponent_for_team0 else (opponent_for_team0, 0)

            # Team 1 plays against each other teams in increasing order 
            # (team1 vs team2 week 1, team1 vs team3 week 2, ...)
            solver_sts.add(
                Or([match_vars[(team_a, team_b, w, p)] for p in range(NUM_PERIODS_PER_WEEK)])
            )
            
            # Fix home/away matches for team 1 (even weeks plays at home, odd weeks plays away)
            if w % 2 == 0:
                if team_a == 0: 
                    solver_sts.add(home_vars[(team_a, team_b)]) 
                else:
                    solver_sts.add(Not(home_vars[(team_a, team_b)])) 
            else: 
                if team_a == 0:
                    solver_sts.add(Not(home_vars[(team_a, team_b)])) 
                else:
                    solver_sts.add(home_vars[(team_a, team_b)]) 
    
    return solver_sts, match_vars, home_vars, home_counts, away_counts, diff_values, total_objective