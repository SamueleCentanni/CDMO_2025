from z3 import *
import time
import math
from circle_matching import circle_matchings
from encoding_utils import heule_exactly_one, at_most_k_seq

# Heavy model based on matrix games_vars[i,j,w,p]=True iff match (i,j) in period p in week w
# Use of Symmetry Breaking constraints and advanced encodings, not use of warm start

class STS_Optimized_Matrix:
    def __init__(self, n, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding
        
        self.solver, self.games_vars, self.home_counts, self.away_counts, self.diff_values, self.total_objective = create_sts_model(
            n, 
            self.exactly_one_encoding, 
            self.at_most_k_encoding,
            symmetry_breaking=True,
        )

    def solve(self, timeout_seconds, random_seed=None, verbose=False, solver_options=True):
        
        if solver_options:
            if random_seed is not None:
                self.solver.set("random_seed", random_seed)
            
            if self.n <= 6:
                self.solver.set("phase_selection", 0)
                self.solver.set("restart_strategy", 0)
            else:
                self.solver.set("phase_selection", 2)
                self.solver.set("restart_factor", 1.2)
                self.solver.set("restart_strategy", 1)

        optimal_objective_value = None
        best_solution_schedule = []
        
        init_time = time.time()
        timeout_timestamp = init_time + timeout_seconds
        
        proven_optimal_final = False 
        solution_found_at_least_once = False 

        if verbose:
            print(f"\n--- Starting Optimization for n={self.n} ---")
            print(f"  Using exactly_one: {self.exactly_one_encoding.__name__}, at_most_k: {self.at_most_k_encoding.__name__}")

        # Iterative Optimization
        while True:
            remaining_time = math.floor(timeout_timestamp - time.time())
            
            if remaining_time <= 0:
                if verbose:
                    print("  Overall timeout reached. Breaking optimization loop.")
                break
            
            self.solver.push()
            self.solver.set("timeout", remaining_time * 1000)
            

            if optimal_objective_value is not None:
                self.solver.add(self.total_objective < optimal_objective_value)
                if verbose:
                    print(f"  Searching for solution with total difference < {optimal_objective_value} (Remaining overall time: {remaining_time}s)...")
            else:
                if verbose:
                    print(f"  Searching for initial solution (Remaining overall time: {remaining_time}s)...")

            status = self.solver.check()
            current_elapsed_time = time.time() - init_time

            if verbose:
                print(f"  Solver iteration returned: {status} (Elapsed: {current_elapsed_time:.2f}s)")

            if status == sat:
                model = self.solver.model()
                current_objective = model.evaluate(self.total_objective).as_long()
                solution_found_at_least_once = True 
                
                if verbose:
                    print(f"    Found solution with total difference = {current_objective}")

                if optimal_objective_value is None or current_objective < optimal_objective_value:
                    optimal_objective_value = current_objective
                    if verbose:
                        print(f"    New best total difference found: {optimal_objective_value}")

                    best_solution_schedule = []
                    
                    for w in range(self.NUM_WEEKS):
                        for p in range(self.NUM_PERIODS_PER_WEEK):
                            for i in range(self.NUM_TEAMS):
                                for j in range(i + 1, self.NUM_TEAMS): 
                                    var_ij = self.games_vars[(i, j, w, p)]
                                    if model.evaluate(var_ij):
                                        best_solution_schedule.append((i+1, j+1, w+1, p+1))
                                        continue
                                    var_ji = self.games_vars[(j, i, w, p)]
                                    if model.evaluate(var_ji):
                                        best_solution_schedule.append((j+1, i+1, w+1, p+1))

                    if verbose:
                        print("    Home/Away counts for this solution:")
                        for i in range(self.NUM_TEAMS):
                            h_count = model.evaluate(self.home_counts[i]).as_long()
                            a_count = model.evaluate(self.away_counts[i]).as_long()
                            d_val = model.evaluate(self.diff_values[i]).as_long()
                            calculated_diff = abs(h_count - a_count)
                            print(f"      Team {i+1}: Home = {h_count}, Away = {a_count}, Diff = {d_val} (Calculated: {calculated_diff})")

                    if optimal_objective_value == self.n: 
                        proven_optimal_final = True 
                        if verbose:
                            print(f"    Lower bound ({self.n}) reached. Optimization complete.")
                        self.solver.pop() 
                        break
                
                self.solver.pop()
                    

            elif status == unsat:
                proven_optimal_final = True 
                if verbose:
                    print("  No better solution found. Optimization complete.")
                self.solver.pop() 
                break

            elif status == unknown:
                if verbose:
                    print("  Solver returned 'unknown' (likely due to timeout during iteration).")
                self.solver.pop() 
                break 

        stat = self.solver.statistics()
        final_stats = {
            'restarts': stat.get_key_value('restarts') if 'restarts' in stat.keys() else 0,
            'max_memory': stat.get_key_value('max memory') if 'max memory' in stat.keys() else 0,
            'mk_bool_var': stat.get_key_value('mk bool var') if 'mk bool var' in stat.keys() else 0,
            'conflicts': stat.get_key_value('conflicts') if 'conflicts' in stat.keys() else 0,
            'solve_time': current_elapsed_time
        }
        
        if verbose:
            print("\n--- Optimization Finished ---")
            print(f"  Optimal Total Difference found: {optimal_objective_value}")
            print("  Final Solver Statistics (from last check):")
            for k, v in final_stats.items():
                print(f"    {k}: {v}")

        # Results
        if proven_optimal_final: 
            if optimal_objective_value is not None:
                return (optimal_objective_value, best_solution_schedule, True,
                        final_stats['solve_time'], final_stats['restarts'],
                        final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
            else:
                if verbose:
                    print("  Problem proven unsatisfiable (UNSAT).")
                return (None, None, True, 
                        final_stats['solve_time'], final_stats['restarts'],
                        final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
        elif solution_found_at_least_once:
            return (optimal_objective_value, best_solution_schedule, False,
                    final_stats['solve_time'], final_stats['restarts'],
                    final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
        else:
            if verbose:
                print("  No solution found at all (timeout or unknown state before any SAT).")
            return (None, None, False,
                    final_stats['solve_time'], final_stats['restarts'],
                    final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
            
            
            
            
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

def create_sts_model(n, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=False, use_circle_matchings=True):
    """
    The model aims to minimize the total imbalance (difference) between home and away matches for all teams.

    Parameters:
        n (int): Number of teams (must be even).
        exactly_one_encoding (Callable): Function that enforces an "exactly one" constraint on a list of Boolean variables.
        at_most_k_encoding (Callable): Function that enforces an "at most k" constraint on a list of Boolean variables.
        symmetry_breaking (bool, optional): If True, enforces symmetry breakings. Default is False.

    Returns:
        solver_sts (z3.Solver): The Z3 solver instance with all variables and constraints.
        games_vars (dict): Dictionary mapping (i, j, w, p) to Boolean variables indicating match scheduling.
        home_counts (list): List of Int variables H_i counting the number of home games for each team.
        away_counts (list): List of Int variables A_i counting the number of away games for each team.
        diff_values (list): List of Int variables D_i representing |H_i - A_i| for each team.
        total_objective (z3.ExprRef): Expression representing the objective to minimize (sum of D_i).
    """
    
    NUM_TEAMS = n
    NUM_WEEKS = NUM_TEAMS - 1
    NUM_PERIODS_PER_WEEK = n // 2
    
    if NUM_TEAMS % 2 != 0:
        raise ValueError(f"Error: The number of teams (n={NUM_TEAMS}) must be an even number.")

    solver_sts = Solver() 

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
    
    # WARM START
    if use_circle_matchings:
        matchings = circle_matchings(NUM_TEAMS)  # dict: week -> list of (i,j)
        
        for w in range(NUM_WEEKS):
            matching = matchings[w]
            # Rendi le coppie non direzionali
            allowed_pairs = set((min(i, j), max(i, j)) for (i, j) in matching)

            for i in range(NUM_TEAMS):
                for j in range(NUM_TEAMS):
                    if i == j:
                        continue
                    if (min(i, j), max(i, j)) not in allowed_pairs:
                        for p in range(NUM_PERIODS_PER_WEEK):
                            if (i, j, w, p) in games_vars:
                                solver_sts.add(Not(games_vars[(i, j, w, p)]))
    
    # --- Symmetry Breaking ---
    if symmetry_breaking and use_circle_matchings:
        # 1. Fissa che team 0 giochi in casa contro team N-1 nel primo periodo della prima settimana
        team_a = 0
        team_b = NUM_TEAMS - 1
        solver_sts.add(games_vars[(team_a, team_b, 0, 0)])

        # 3. Lexicographical ordering dei match nella prima settimana
        w = 0  # prima settimana
        matches_in_week = sorted([(i, j) if i < j else (j, i) for (i, j) in matchings[w]])
        bool_vectors = []
        for (i, j) in matches_in_week:
            vec = [games_vars[(i, j, w, p)] for p in range(NUM_PERIODS_PER_WEEK) if (i, j, w, p) in games_vars]
            bool_vectors.append(vec)

        for a in range(len(bool_vectors) - 1):
            solver_sts.add(lex_less_bool(bool_vectors[a], bool_vectors[a + 1]))
    
    
                
    # --- Optimization Variables ---
    home_counts = [Int(f'H_{i+1}') for i in range(NUM_TEAMS)]
    away_counts = [Int(f'A_{i+1}') for i in range(NUM_TEAMS)]
    diff_values = [Int(f'D_{i+1}') for i in range(NUM_TEAMS)] 

    # Constraints for home/away counts
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
        

        solver_sts.add(diff_values[i] == If(home_counts[i] >= away_counts[i],
                                       home_counts[i] - away_counts[i],
                                       away_counts[i] - home_counts[i]))

    # Total difference (objective function) 
    total_objective = Sum(diff_values)
    
    # --- LOWER BOUND CONSTRAINT ---
    # Since n is always even, NUM_WEEKS (n-1) is always odd.
    # The minimum difference |H-A| for a single team is 1.
    # So, the sum of differences for all N_TEAMS is at least N_TEAMS * 1.
    lower_bound_total_diff = NUM_TEAMS 
    print(f"  Adding lower bound constraint: total_objective >= {lower_bound_total_diff}")
    solver_sts.add(total_objective >= lower_bound_total_diff)

    return solver_sts, games_vars, home_counts, away_counts, diff_values, total_objective