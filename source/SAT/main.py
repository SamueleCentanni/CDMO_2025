import os
import argparse
from itertools import combinations
from z3 import *
import math
import time
import json


# --------------------------------------------------------------
# EXACTLY ONE ENCODINGS
# --------------------------------------------------------------

# Naive/Pairwise (NP)
def at_least_one_np(bool_vars):
    return Or(bool_vars)

def at_most_one_np(bool_vars, name=""):
    return And([Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)])

def exactly_one_np(bool_vars, name=""):
    return And(at_least_one_np(bool_vars), at_most_one_np(bool_vars, name))

#--------------------------------------------------------------------------------------------------------------------------------------------------------

# Binary Encoding (BW)
def toBinary(num, length=None):
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

# Heule Encoding   

global_most_counter = 0 

def heule_at_most_one(bool_vars):
    if len(bool_vars) <= 4: # Base case: use pairwise encoding
        return And([Not(And(pair[0], pair[1])) for pair in combinations(bool_vars, 2)])
    else:
        global global_most_counter
        global_most_counter += 1
        aux_var = Bool(f'y_amo_{global_most_counter}') 

        # Split into roughly 1/4 and 3/4, with an auxiliary variable
        return And(at_most_one_np(bool_vars[:3] + [aux_var]), heule_at_most_one([Not(aux_var)] + bool_vars[3:]))
    

def heule_exactly_one(bool_vars, name=''):
    return And(heule_at_most_one(bool_vars), at_least_one_np(bool_vars))
#--------------------------------------------------------------------------------------------------------------------------------------------------------

# --------------------------------------------------------------
# AT MOST K (2) ENCODINGS
# --------------------------------------------------------------

# General K-Encoding (NP - Direct Encoding)
def at_most_k_np(bool_vars, k, name=""):
    if k >= len(bool_vars): return BoolVal(True) 
    if k < 0: return BoolVal(False)
    return And([Or([Not(x) for x in X]) for X in combinations(bool_vars, k + 1)])


# General K-Encoding (SEQ - Sequential Counter Encoding)
def at_most_k_seq(bool_vars, k, name=''):
    constraints = []
    n = len(bool_vars)
    
    if n == 0: return BoolVal(True)
    if k == 0: return And([Not(v) for v in bool_vars])
    if k >= n: return BoolVal(True)

    s = [[Bool(f"s_{name}_{i}_{j}") for j in range(k)] for i in range(n-1)] 
    
    constraints.append(Or(Not(bool_vars[0]), s[0][0])) 
    for j in range(1, k):
        constraints.append(Not(s[0][j]))

    for i in range(1, n-1):
        constraints.append(Or(Not(s[i-1][0]), s[i][0]))
        constraints.append(Or(Not(bool_vars[i]), s[i][0]))

        for j in range(1, k):
            constraints.append(Or(Not(s[i-1][j]), s[i][j]))
            constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][j-1]), s[i][j]))
        
        constraints.append(Or(Not(bool_vars[i]), Not(s[i-1][k-1])))
    constraints.append(Or(Not(bool_vars[n-1]), Not(s[n-2][k-1])))
    return And(constraints)

#--------------------------------------------------------------------------------------------------------------------------------------------------------

# Totalizer Encoding
def totalizer_merge(left_sum, right_sum, name_prefix, depth, constraints):
    """Merges two partial sums for the totalizer encoding."""
    merged = [Bool(f"{name_prefix}_s_{depth}_{i}") for i in range(len(left_sum) + len(right_sum))]
    
    for i in range(len(left_sum)):
        constraints.append(Implies(left_sum[i], merged[i]))
    for i in range(len(right_sum)):
        constraints.append(Implies(right_sum[i], merged[i]))
    for i in range(len(left_sum)):
        for j in range(len(right_sum)):
            if i + j + 1 < len(merged):
                constraints.append(Implies(And(left_sum[i], right_sum[j]), merged[i + j + 1]))
    return merged

def at_most_k_totalizer(bool_vars, k, name=''):
    """At most k using totalizer encoding."""
    constraints = []
    n = len(bool_vars)
    if k >= n: return BoolVal(True)
    if k < 0: return BoolVal(False)
    if n == 0: return BoolVal(True)

    current_level = [[v] for v in bool_vars] # each boolean variable is a leaf
    depth = 0
    
    # totalizer tree
    while len(current_level) > 1:  # when we encounter the root, we stop
        next_level = []
        for i in range(0, len(current_level), 2):
            if i + 1 == len(current_level):
                next_level.append(current_level[i])
            else:
                left = current_level[i]
                right = current_level[i + 1]
                merged = totalizer_merge(left, right, name, depth, constraints)
                next_level.append(merged)
                depth += 1 # to give unique names in the totalizer_merge
        current_level = next_level

    total_sum = current_level[0]
    
    # at most k implementation
    for i in range(k, len(total_sum)):
        constraints.append(Not(total_sum[i])) # i = at least i+1 variables are true

    return And(constraints)
#--------------------------------------------------------------------------------------------------------------------------------------------------------



def convert_to_matrix(n, solution):
    """
    Converts the solution (list of tuples) into a matrix format.
    Assumes solution uses 1-based indexing for weeks and periods.
    """
    num_periods = n // 2
    num_weeks = n - 1
    matrix = [[None for _ in range(num_weeks)] for _ in range(num_periods)]
    for h, a, w, p in solution:
        # Use 0-based indexing for the matrix
        matrix[p - 1][w - 1] = [h, a]
    return matrix

def save_results_as_json(n, results, model_name, output_dir="/res/SAT"):
    """
    Saves the results dictionary to a JSON file.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    json_path = os.path.join(output_dir, f"{n}.json")
    
    json_obj = {}
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            try:
                json_obj = json.load(f)
            except json.JSONDecodeError:
                json_obj = {}
                
    result = {}
    result[model_name] = results
    
    for method, res in result.items():
        runtime = res.get("time", 300.0)
        
        time_field = 300 if not res.get("optimal") else math.floor(runtime)
        sol = res.get("sol")
        matrix = convert_to_matrix(n, sol) if sol else []
        
        json_obj[method] = {
            "time": time_field,
            "optimal": res.get("optimal"),
            "obj": res.get("obj"),
            "sol": matrix,
        }
    
    with open(json_path, "w") as f:
        json.dump(json_obj, f, indent=1)

def print_weekly_schedule(match_list, num_teams):
    """
    Prints a weekly schedule in a human-readable format.
    Assumes match_list contains 1-based teams, weeks, and periods.
    """
    num_weeks = num_teams - 1
    num_periods = num_teams // 2

    print("\n--- Sport Tournament Scheduler ---")
    print(f"Number of Teams: {num_teams}")
    print(f"Number of Weeks: {num_weeks}")
    print(f"Periods per Week: {num_periods}")
    print("---------------------------\n")
    
    if match_list is None:
        print("No solution was found")
        return

    # Use a dictionary to organize the schedule by week and period
    schedule = {}
    for home_team, away_team, week, period in match_list:
        schedule[(week, period)] = (home_team, away_team)

    for w_idx in range(1, num_weeks + 1):
        print(f"Week {w_idx}:")
        for p_idx in range(1, num_periods + 1):
            match = schedule.get((w_idx, p_idx))
            if match:
                home_team, away_team = match
                print(f"  Period {p_idx}: Team {home_team} (Home) vs Team {away_team} (Away)")
            else:
                print(f"  Period {p_idx}: [No Scheduled Matches]")
        print()
    
    print("--- END SCHEDULE ---\n")
    
def circle_matchings(n):
    """
    Generates a schedule using the Circle Method for n teams.
    Returns a dictionary of week (0-based) to a list of match-ups.
    """
    pivot, circle = n - 1, list(range(n - 1))
    weeks = n - 1
    m = {}
    for w in range(weeks):
        ms = [(pivot, circle[w])]
        for k in range(1, n // 2):
            i = circle[(w + k) % (n - 1)]
            j = circle[(w - k + (n - 1)) % (n - 1)]
            ms.append((i, j))
        m[w] = ms
    return m

def lex_less_bool(curr, next):
    """
    Implements a lexicographical less-than constraint for two lists of boolean variables.
    """
    conditions = []
    for i in range(len(curr)):
        prefix_equal = [curr[j] == next[j] for j in range(i)]
        condition = And(prefix_equal + [curr[i], Not(next[i])])
        conditions.append(condition)
    return Or(conditions)

def create_sts_model(n, max_diff_k, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=True):
    """
    Creates a Z3 model for the STS problem with a fixed calendar, using
    Pseudo-Boolean constraints for encoding. The model enforces that
    the home/away imbalance for any team does not exceed max_diff_k.

    Args:
        n (int): Number of teams (must be even).
        max_diff_k (int): The maximum allowed home/away imbalance.
        symmetry_breaking (bool): Whether to apply symmetry breaking constraints.

    Returns:
        tuple: (solver, match_period_vars, home_vars, pair_to_week)
    """
    if n % 2 != 0:
        raise ValueError("The number of teams must be even.")
        
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
    match_period_vars = {}
    for (i, j) in pair_to_week:
        for p in range(NUM_PERIODS_PER_WEEK):
            match_period_vars[(i, j, p)] = Bool(f"m_{i}_{j}_p{p}")

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
        solver.add(match_period_vars[(team_a, team_b, 0)])

        # SB2: Team 0 plays at home in even weeks, away in odd weeks
        for (i, j), w in pair_to_week.items():
            if i == 0:
                solver.add(home_vars[(i, j)] if w % 2 == 0 else Not(home_vars[(i, j)]))
            elif j == 0:
                solver.add(Not(home_vars[(i, j)]) if w % 2 == 0 else home_vars[(i, j)])

        # SB3: Lexicographical ordering of matches in week 0
        matches_in_week0 = sorted([(i, j) if i < j else (j, i) for (i, j) in week_matchings[0]])
        if len(matches_in_week0) > 1:
            bool_vectors = [
                [match_period_vars[(i, j, p)] for p in range(NUM_PERIODS_PER_WEEK)]
                for (i, j) in matches_in_week0
            ]
            for a in range(len(bool_vectors) - 1):
                solver.add(lex_less_bool(bool_vectors[a], bool_vectors[a + 1]))

    # === Optimization constraint for SAT: max_diff_k ===
    for t in range(NUM_TEAMS):
        home_games_for_t = []
        for (i, j), _ in pair_to_week.items():
            for p in range(NUM_PERIODS_PER_WEEK):
                mp = match_period_vars[(i, j, p)]
                if t == i:
                    home_games_for_t.append(And(mp, home_vars[(i, j)]))
                elif t == j:
                    home_games_for_t.append(And(mp, Not(home_vars[(i, j)])))

        NUM_GAMES = n - 1
        
        upper_bound = math.floor((NUM_GAMES + max_diff_k) / 2)
        lower_bound = math.ceil((NUM_GAMES - max_diff_k) / 2)

        solver.add(PbLe([(v, 1) for v in home_games_for_t], upper_bound))
        solver.add(PbGe([(v, 1) for v in home_games_for_t], lower_bound))
    
    return solver, match_period_vars, home_vars, pair_to_week

def solve_sts_optimization(n, timeout_seconds, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=True, verbose=False):
    """
    Solves the STS problem by performing a binary search on the maximum home/away
    imbalance (MinMax objective).
    """
    if n % 2 != 0:
        raise ValueError("The number of teams must be even.")
        
    NUM_WEEKS = n - 1
    
    low = 1
    high = NUM_WEEKS
    optimal_diff_MinMax = None
    best_solution_model = None
    best_solution_vars = None
    solution_found_at_least_once = False
    proven_unsat = False

    init_time = time.time()
    
    if verbose:
        print(f"\n--- Optimization for n={n} started ---")

    # Binary search
    while low <= high:
        current_elapsed_time = time.time() - init_time
        remaining_time = timeout_seconds - current_elapsed_time
        
        if remaining_time <= 0:
            if verbose:
                print("Global timeout reached.")
            break
            
        k = (low + high) // 2 # binary search 
        
        if verbose:
            print(f"Testing max_diff <= {k}. Remaining time: {remaining_time:.2f}s...")
        
        solver, match_period_vars, home_vars, pair_to_week = create_sts_model(
            n=n,
            max_diff_k=k,
            exactly_one_encoding=exactly_one_encoding,
            at_most_k_encoding=at_most_k_encoding,
            symmetry_breaking=symmetry_breaking
        )
        solver.set("random_seed", 42)
        solver.set("timeout", int(remaining_time * 1000))
        
        status = solver.check()
        
        current_elapsed_time = time.time() - init_time
        
        if verbose:
            current_elapsed_time = current_elapsed_time if current_elapsed_time <= 300 else 300
            print(f"  Solver result for k={k}: {status}")
            
        if status == sat:
            model = solver.model()
            optimal_diff_MinMax = k
            best_solution_model = model
            best_solution_vars = (match_period_vars, home_vars, pair_to_week)
            solution_found_at_least_once = True
            high = k - 1
            if verbose:
                print(f"  Found a solution with max_diff <= {k}. Trying for a smaller value.")
                
        elif status == unsat:
            proven_unsat = True
            break
                
        else: 
            if verbose:
                print("  Solver returned 'unknown'.")
            break

    stat = solver.statistics()
    final_stats = {
        'restarts': stat.get_key_value('restarts') if 'restarts' in stat.keys() else 0,
        'max_memory': stat.get_key_value('max memory') if 'max memory' in stat.keys() else 0,
        'mk_bool_var': stat.get_key_value('mk bool var') if 'mk bool var' in stat.keys() else 0,
        'conflicts': stat.get_key_value('conflicts') if 'conflicts' in stat.keys() else 0,
    }
    
    solve_time = time.time() - init_time

    best_solution_schedule = []
    proven_optimal_final = False

    if best_solution_model:
        match_period_vars, home_vars, pair_to_week = best_solution_vars
        
        for (i, j, p), var in match_period_vars.items():
            if is_true(best_solution_model.evaluate(var)):
                home_vars_key = (i, j) if i < j else (j, i)
                is_home = is_true(best_solution_model.evaluate(home_vars[home_vars_key]))
                
                if i < j:
                    home_team_idx = i if is_home else j
                    away_team_idx = j if is_home else i
                else:
                    home_team_idx = i if is_home else j
                    away_team_idx = j if is_home else i

                week_idx = pair_to_week[home_vars_key]
                
                best_solution_schedule.append((home_team_idx + 1, away_team_idx + 1, week_idx + 1, p + 1))

        if optimal_diff_MinMax is not None and optimal_diff_MinMax == 1:
            proven_optimal_final = True
            
    solve_time = solve_time if solve_time <= 300 else 300
            
    if proven_optimal_final:
        result = {
            'obj': optimal_diff_MinMax,
            'sol': best_solution_schedule,
            'optimal': True,
            'time': solve_time,
            'restart': final_stats['restarts'],
            'max_memory': final_stats['max_memory'],
            'mk_bool_var': final_stats['mk_bool_var'],
            'conflicts': final_stats['conflicts']
        }
        return result
    elif proven_unsat:
        result = {
            'obj': None,
            'sol': best_solution_schedule,
            'optimal': True,
            'time': solve_time,
            'restart': final_stats['restarts'],
            'max_memory': final_stats['max_memory'],
            'mk_bool_var': final_stats['mk_bool_var'],
            'conflicts': final_stats['conflicts']
        }
        return result
    elif solution_found_at_least_once:
        result = {
            'obj': optimal_diff_MinMax,
            'sol': best_solution_schedule,
            'optimal': False,
            'time': solve_time,
            'restart': final_stats['restarts'],
            'max_memory': final_stats['max_memory'],
            'mk_bool_var': final_stats['mk_bool_var'],
            'conflicts': final_stats['conflicts']
        }
        return result
    else:
        result = {
            'obj': None,
            'sol': None,
            'optimal': False,
            'time': solve_time,
            'restart': final_stats['restarts'],
            'max_memory': final_stats['max_memory'],
            'mk_bool_var': final_stats['mk_bool_var'],
            'conflicts': final_stats['conflicts']
        }
        return result
    
    
def solve_sts_decisional(n, max_diff_k, timeout_seconds, exactly_one_encoding, at_most_k_encoding, symmetry_breaking=True, verbose=False):
    """
    Solves the STS decisional problem: finds ONE solution for a given max_diff_k.
    Does NOT perform optimization.
    """
    if verbose:
        print(f"\n--- Decisional solver for n={n} ---")

    init_time = time.time()

    solver, match_period_vars, home_vars, pair_to_week = create_sts_model(
        n=n,
        max_diff_k=max_diff_k,
        exactly_one_encoding=exactly_one_encoding,
        at_most_k_encoding=at_most_k_encoding,
        symmetry_breaking=symmetry_breaking
    )
    
    solver.set("random_seed", 42)
    solver.set("timeout", int(timeout_seconds * 1000))
    
    status = solver.check()
    solve_time = time.time() - init_time
    
    final_stats = solver.statistics()
    stats_dict = {
        'restarts': final_stats.get_key_value('restarts') if 'restarts' in final_stats.keys() else 0,
        'max_memory': final_stats.get_key_value('max memory') if 'max memory' in final_stats.keys() else 0,
        'mk_bool_var': final_stats.get_key_value('mk bool var') if 'mk bool var' in final_stats.keys() else 0,
        'conflicts': final_stats.get_key_value('conflicts') if 'conflicts' in final_stats.keys() else 0,
    }
    best_solution_schedule = []
    
    if status == sat:
        model = solver.model()
        
        
        for (i, j, p), var in match_period_vars.items():
            if is_true(model.evaluate(var)):
                home_vars_key = (i, j) if i < j else (j, i)
                is_home = is_true(model.evaluate(home_vars[home_vars_key]))
                
                if i < j:
                    home_team_idx = i if is_home else j
                    away_team_idx = j if is_home else i
                else:
                    home_team_idx = i if is_home else j
                    away_team_idx = j if is_home else i

                week_idx = pair_to_week[home_vars_key]
                
                best_solution_schedule.append((home_team_idx + 1, away_team_idx + 1, week_idx + 1, p + 1))
    
    solve_time = solve_time if solve_time <= 300 else 300
    result = {
        'obj': None,
        'sol': best_solution_schedule,
        'optimal': True,
        'time': solve_time,
        'restart': stats_dict['restarts'],
        'max_memory': stats_dict['max_memory'],
        'mk_bool_var': stats_dict['mk_bool_var'],
        'conflicts': stats_dict['conflicts']
    }
    return result


import argparse
import re
from itertools import product

def parse_n_teams(n_input):
    """
    Parses the input for -n argument, allowing range input like 2-18.
    Ensures only even numbers are returned.
    """
    result = set()
    for item in n_input:
        if re.match(r"^\d+-\d+$", item):  # range type: 2-18
            start, end = map(int, item.split("-"))
            for n in range(start, end + 1):
                if n % 2 == 0:
                    result.add(n)
        else:  # single value
            try:
                n = int(item)
                if n % 2 == 0:
                    result.add(n)
                else:
                    print(f"[WARNING] Skipping odd number: {n}")
            except ValueError:
                print(f"[WARNING] Invalid value for -n: {item}")
    return sorted(result)

def main():
    parser = argparse.ArgumentParser(description="Sport Tournament Scheduler using Z3 solvers.")
    parser.add_argument(
        "-n", "--n_teams",
        type=str,
        nargs='+',
        default=["2-20"],
        help="List of even numbers or ranges like 2-18 for number of teams to test."
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each solver instance."
    )
    parser.add_argument(
        "--exactly_one_encoding",
        type=str,
        choices=["np", "bw", "seq", "heule"],
        help="Encoding for exactly-one constraints."
    )
    parser.add_argument(
        "--at_most_k_encoding",
        type=str,
        choices=["np", "seq", "totalizer"],
        help="Encoding for at-most-k constraints."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all combinations of encoding methods."
    )
    parser.add_argument(
        "--run_decisional",
        action="store_true",
        help="Run the decisional solver."
    )
    parser.add_argument(
        "--run_optimization",
        action="store_true",
        help="Run the optimization solver."
    )
    

    parser.add_argument(
        "--sb",
        dest="sb",
        action="store_true",
        help="Enable symmetry breaking."
    )
    parser.add_argument(
        "--no-sb",
        dest="sb",
        action="store_false",
        help="Disable symmetry breaking."
    )
    parser.set_defaults(sb=None)

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    parser.add_argument(
        "--save_json",
        action='store_true',
        help="Save solver results to JSON files."
    )

    args = parser.parse_args()

    # Parse and validate number of teams
    args.n_teams = parse_n_teams(args.n_teams)

    # Encoding functions
    exactly_one_encodings = {
        "np": exactly_one_np,
        "bw": exactly_one_bw,
        "seq": exactly_one_seq,
        "heule": heule_exactly_one,
    }
    at_most_k_encodings = {
        "np": at_most_k_np,
        "seq": at_most_k_seq,
        "totalizer": at_most_k_totalizer,
    }

    if args.all:
        allowed_pairs = [
            ("np", "np"),
            ("heule", "seq"),
            ("heule", "totalizer")
        ]
        encoding_combinations = [
            ((eo, exactly_one_encodings[eo]), (ak, at_most_k_encodings[ak]))
            for eo, ak in allowed_pairs
        ]
    else:
        if not args.exactly_one_encoding or not args.at_most_k_encoding:
            print("Error: You must specify both --exactly_one_encoding and --at_most_k_encoding, or use --all.")
            return
        encoding_combinations = [(
            (args.exactly_one_encoding, exactly_one_encodings[args.exactly_one_encoding]),
            (args.at_most_k_encoding, at_most_k_encodings[args.at_most_k_encoding])
        )]

    if not args.run_decisional and not args.run_optimization:
        print("Error: You must choose to run either --run_decisional or --run_optimization (or both).")
        parser.print_help()
        return

    timeout = args.timeout - 1
    if args.sb is None:
        sb_options = [True, False]
    else:
        sb_options = [args.sb]

    for sb in sb_options:
        sb_name = "sb" if sb else "no_sb"
        for (eo_name, eo_func), (ak_name, ak_func) in encoding_combinations:
            name_prefix = f"{eo_name}_{ak_name}"

            if args.run_decisional:
                # print(f"\n=== Decisional Solver | {eo_name} + {ak_name} | Symmetry: {sb_name} ===\n")
                for n in args.n_teams:
                    model_name = f"decisional_{name_prefix}_{sb_name}"
                    try:
                        results = solve_sts_decisional(
                            n,
                            max_diff_k=n-1,
                            exactly_one_encoding=eo_func,
                            at_most_k_encoding=ak_func,
                            timeout_seconds=timeout,
                            symmetry_breaking=sb,
                            verbose=args.verbose
                        )
                    except ValueError as e:
                        print(f"Skipping n={n}: {e}")
                        continue

                    if args.save_json:
                        save_results_as_json(n, model_name=model_name, results=results)

                    if results['sol'] is not None:
                        if os.path.exists("/.dockerenv"):
                            os.system(f"echo '[Decisional Result] n={n} | time={results['time']}'")
                        else:
                            print(f"[Decisional Result] n={n} | time={results['time']}")
                        # print_weekly_schedule(results['sol'], n)
                    else:
                        print(f"[!] No solution found for n={n}")

            if args.run_optimization:
                print(f"\n=== Optimization Solver | {eo_name} + {ak_name} | Symmetry: {sb_name} ===\n")
                for n in args.n_teams:
                    model_name = f"optimization_{name_prefix}_{sb_name}"
                    try:
                        results = solve_sts_optimization(
                            n,
                            exactly_one_encoding=eo_func,
                            at_most_k_encoding=ak_func,
                            timeout_seconds=timeout,
                            symmetry_breaking=sb,
                            verbose=args.verbose
                        )
                    except ValueError as e:
                        print(f"Skipping n={n}: {e}")
                        continue

                    if args.save_json:
                        save_results_as_json(n, model_name=model_name, results=results)

                    if results['sol'] is not None:
                        if os.path.exists("/.dockerenv"):
                            os.system(f"echo '[Optimization Result] n={n} | obj={results['obj']} | time={results['time']}'")
                        else:
                            print(f"[Optimization Result] n={n} | obj={results['obj']} | time={results['time']}")
                        # print_weekly_schedule(results['sol'], n)
                    else:
                        print(f"[!] No solution found for n={n}")

if __name__ == "__main__":
    main()