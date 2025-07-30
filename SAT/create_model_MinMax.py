from z3 import *
from circle_matching import circle_matchings  

def Max(vs):
    m = vs[0]
    for v in vs[1:]:
        m = If(v > m, v, m)
    return m

def lex_less_bool(curr, next):
        # curr, next: lists of Bools
        conditions = []
        for i in range(len(curr)):
            if i == 0:
                # At position 0: curr[0] = True and next[0] = False
                condition = And(curr[i], Not(next[i]))
            else:
                # At position i: all previous positions equal, curr[i] = True, next[i] = False
                prefix_equal = [curr[j] == next[j] for j in range(i)]
                condition = And(prefix_equal + [curr[i], Not(next[i])])
            conditions.append(condition)
        return Or(conditions)

def create_sts_model_MinMax(n, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=True):
    """
    Create a Sports Tournament Scheduling (STS) model using Boolean variables,
    aiming to minimize the maximum home/away imbalance across all teams.

    Args:
        n (int): Number of teams (must be even).
        exactly_one_encoding (function): Function to encode an exactly-one constraint.
        at_most_k_encoding (function): Function to encode an at-most-k constraint.
        symmetry_breaking (bool): Whether to apply symmetry breaking constraints.

    Returns:
        tuple: (solver, match_period_vars, home_vars, home_counts, away_counts, 
                diff_values, max_diff, pair_to_week)
    """
    NUM_TEAMS = n
    NUM_WEEKS = n - 1
    NUM_PERIODS_PER_WEEK = n // 2

    solver = Solver()

    # --- Fixed calendar using the circle method ---
    week_matchings = circle_matchings(NUM_TEAMS)
    pair_to_week = {}
    for w, matches in week_matchings.items():
        for (i, j) in matches:
            if i > j:
                i, j = j, i
            pair_to_week[(i, j)] = w

    # === Boolean Variables ===

    # match_period_vars[(i,j,p)] is True if match (i,j) is played in period p
    match_period_vars = {}
    for (i, j) in pair_to_week:
        for p in range(NUM_PERIODS_PER_WEEK):
            match_period_vars[(i, j, p)] = Bool(f"m_{i}_{j}_p{p}")

    # home_vars[(i,j)] is True if team i plays at home vs team j
    home_vars = {}
    for i in range(NUM_TEAMS):
        for j in range(i + 1, NUM_TEAMS):
            home_vars[(i, j)] = Bool(f"home_{i}_{j}")

    # === Base Constraints ===

    # 1. Each match (i,j) is assigned to exactly one period
    for (i, j) in pair_to_week:
        solver.add(exactly_one_encoding(
            [match_period_vars[(i, j, p)] for p in range(NUM_PERIODS_PER_WEEK)],
            f"match_once_{i}_{j}"
        ))

    # 2. Each period in each week contains exactly one match
    for w in range(NUM_WEEKS):
        week_matches = week_matchings[w]
        for p in range(NUM_PERIODS_PER_WEEK):
            vars_for_slot = [] 
            for (i, j) in week_matches:
                if i > j:
                    i, j = j, i
                vars_for_slot.append(match_period_vars[(i, j, p)])
            solver.add(exactly_one_encoding(vars_for_slot, f"one_match_per_slot_w{w}_p{p}"))

    # 3. Each team plays at most twice in the same period (over the whole tournament)
    for t in range(NUM_TEAMS):
        for p in range(NUM_PERIODS_PER_WEEK):
            appearances = []
            for (i, j), w in pair_to_week.items():
                if t == i or t == j:
                    appearances.append(match_period_vars[(i, j, p)])
            solver.add(at_most_k_encoding(appearances, 2, f"team_{t}_max2_in_p{p}"))

    # === Symmetry Breaking Constraints ===
    if symmetry_breaking:
        # SB1: Force match (0, n-1) to be in the first period
        team_a, team_b = 0, NUM_TEAMS - 1
        w = pair_to_week[(team_a, team_b)]
        solver.add(match_period_vars[(team_a, team_b, 0)])

        # SB2: Team 0 plays at home in even weeks, away in odd weeks
        for (i, j), w in pair_to_week.items():
            if i == 0:
                solver.add(home_vars[(i, j)] if w % 2 == 0 else Not(home_vars[(i, j)]))
            elif j == 0:
                solver.add(Not(home_vars[(i, j)]) if w % 2 == 0 else home_vars[(i, j)])

        # SB3: Lexicographical ordering of matches in week 0
        matches_in_week0 = sorted([(i, j) if i < j else (j, i) for (i, j) in week_matchings[0]])
        bool_vectors = [
            [match_period_vars[(i, j, p)] for p in range(NUM_PERIODS_PER_WEEK)]
            for (i, j) in matches_in_week0
        ]
        for a in range(len(bool_vectors) - 1):
            solver.add(lex_less_bool(bool_vectors[a], bool_vectors[a + 1]))

    # === Optimization: Balance home vs away matches ===

    home_counts = [Int(f"H_{i}") for i in range(NUM_TEAMS)]
    away_counts = [Int(f"A_{i}") for i in range(NUM_TEAMS)]
    diff_values = [Int(f"D_{i}") for i in range(NUM_TEAMS)]

    for t in range(NUM_TEAMS):
        home_exprs = []
        away_exprs = []
        for (i, j), _ in pair_to_week.items():
            for p in range(NUM_PERIODS_PER_WEEK):
                mp = match_period_vars[(i, j, p)]
                if t == i:
                    home_exprs.append(And(mp, home_vars[(i, j)]))
                    away_exprs.append(And(mp, Not(home_vars[(i, j)])))
                elif t == j:
                    home_exprs.append(And(mp, Not(home_vars[(i, j)])))
                    away_exprs.append(And(mp, home_vars[(i, j)]))
        solver.add(home_counts[t] == Sum([If(e, 1, 0) for e in home_exprs]))
        solver.add(away_counts[t] == Sum([If(e, 1, 0) for e in away_exprs]))
        solver.add(diff_values[t] == Abs(home_counts[t] - away_counts[t]))
        solver.add(home_counts[t] + away_counts[t] == NUM_WEEKS)

    # === Objective: Minimize the maximum imbalance ===
    # A tight upper bound is exactly NUM_WEEKS since, in the worse case scenario, a team plays all its matches 
    # away (or at home)
    # A tight lower bound is exactly one, since in the best case scenario, the difference between matches played at home
    # and matches played away is exaclty one (as NUM_WEEKS is always odd)
    max_diff = Max(diff_values)
    solver.add(max_diff >= 1)
    solver.add(max_diff <= NUM_WEEKS)

    return solver, match_period_vars, home_vars, home_counts, away_counts, diff_values, max_diff, pair_to_week



'''
from z3 import *
from circle_matching import circle_matchings

def Max(vs):
  m = vs[0]
  for v in vs[1:]:
    m = If(v > m, v, m)
  return m

def lex_less_bool(curr, next):
        # curr, next: lists of Bools
        conditions = []
        for i in range(len(curr)):
            if i == 0:
                # At position 0: curr[0] = True and next[0] = False
                condition = And(curr[i], Not(next[i]))
            else:
                # At position i: all previous positions equal, curr[i] = True, next[i] = False
                prefix_equal = [curr[j] == next[j] for j in range(i)]
                condition = And(prefix_equal + [curr[i], Not(next[i])])
            conditions.append(condition)
        return Or(conditions)

def create_sts_model_MinMax(n, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=False, use_circle_matchings=True):
    """
    It introduces optimization variables to count home/away games per team and minimize the worst imbalance.

    Parameters:
        n (int): Number of teams (must be even).
        exactly_one_encoding (Callable): Function that applies an "exactly one" constraint over a list of Boolean variables.
        at_most_k_encoding (Callable): Function that applies an "at most k" constraint over a list of Boolean variables.
        symmetry_breaking (bool, optional): If True, adds symmetry-breaking constraints to reduce solution space. Default is False.

    Returns:
        solver_sts (z3.Solver): The Z3 solver instance with all declared variables and constraints.
        match_vars (dict): Mapping (i, j, w, p) → Bool indicating whether team i plays team j in week w and period p (i < j).
        home_vars (dict): Mapping (i, j) → Bool indicating whether team i plays at home against team j (i < j).
        home_counts (list): List of Int variables H_i counting the number of home games for each team i.
        away_counts (list): List of Int variables A_i counting the number of away games for each team i.
        diff_values (list): List of Int variables D_i representing |H_i - A_i| for each team i.
        new_total_objective (z3.ExprRef): Objective function representing the maximum imbalance (max D_i) to minimize.
    """
    
    
    NUM_TEAMS = n
    NUM_WEEKS = NUM_TEAMS - 1
    NUM_PERIODS_PER_WEEK = n // 2
    
    if NUM_TEAMS % 2 != 0:
        raise ValueError(f"Error: The number of teams (n={NUM_TEAMS}) must be even.")
    
    solver_sts = Solver() 
    
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
    
 
    # --- Warm Start ---
    if use_circle_matchings:
        week_matchings = circle_matchings(NUM_TEAMS)
        for w in range(NUM_WEEKS):
            allowed_pairs = set()
            # ordered allowed pairs from warm start
            for (i, j) in week_matchings[w]:
                if i < j:
                    allowed_pairs.add((i, j))
                else:
                    allowed_pairs.add((j, i))
            
            for i in range(NUM_TEAMS):
                for j in range(i+1, NUM_TEAMS):
                    # remove pairs (i,j) which are not allowed by the warm start
                    if (i, j) not in allowed_pairs:
                        for p in range(NUM_PERIODS_PER_WEEK):
                            solver_sts.add(Not(match_vars[(i, j, w, p)]))
    
    
    # --- Symmetry Breaking ---
    if symmetry_breaking and use_circle_matchings:
        
        # --- SB 1 ---
        team_a = 0
        team_b = NUM_TEAMS-1
        solver_sts.add(Or(match_vars[(team_a,team_b,0,0)]))
        
        # --- SB 2 ---
        # team 1 plays at home even weeks and away odd weeks
        for w in range(NUM_WEEKS):
            for (i, j) in week_matchings[w]:
                if i == 0:
                    if w % 2 == 0:
                        solver_sts.add(home_vars[(0, j)])
                    else:
                        solver_sts.add(Not(home_vars[(0, j)]))
                elif j == 0:
                    if w % 2 == 0:
                        solver_sts.add(Not(home_vars[(j, i)]))
                    else:
                        solver_sts.add(home_vars[(j, i)])
        
        # --- SB 3 ---
        w = 0  
        matches_in_week = sorted([ (i,j) if i < j else (j,i) for (i,j) in week_matchings[w] ])
        bool_vectors = []
        for (i, j) in matches_in_week:
            vec = [match_vars[(i,j,w,p)] for p in range(NUM_PERIODS_PER_WEEK)]
            bool_vectors.append(vec)

        for a in range(len(bool_vectors) - 1):
            solver_sts.add(lex_less_bool(bool_vectors[a], bool_vectors[a+1]))



   
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
                        match_var = match_vars[(team_idx, opp_idx, w, p)] 
                        h_var_pair = home_vars[(team_idx, opp_idx)] 
                        
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
    # total_objective = Sum(diff_values)
    new_total_objective = Max(diff_values)
    
    # --- LOWER BOUND CONSTRAINT ---
    # Since n is always even, NUM_WEEKS (n-1) is always odd.
    # The minimum difference |H-A| for a single team is 1.
    lower_bound = 1
    solver_sts.add(new_total_objective >= lower_bound)
    
    # --- UPPER BOUND CONSTRAINT ---
    # since for each team there are at most N-1 matches, the 
    # upper bound should be exactly N-1 (all matches played either away or at home)
    upper_bound = NUM_WEEKS
    solver_sts.add(new_total_objective <= upper_bound)

                    
    return solver_sts, match_vars, home_vars, home_counts, away_counts, diff_values, new_total_objective
'''