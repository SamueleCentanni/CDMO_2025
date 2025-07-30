from z3 import *
import time
import math
from create_model_MinMax import create_sts_model_MinMax  
from encoding_utils import heule_exactly_one, at_most_k_seq

# Light model and advanced encodings
# Use of different optimization function: Min(Max(Diff))
# Use of Symmetry Breaking constraints 

class STS_Different_Optimized_Model:
    def __init__(self, n, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = n - 1
        self.NUM_PERIODS_PER_WEEK = n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding

        (
            self.solver,
            self.match_period_vars,
            self.home_vars,
            self.home_counts,
            self.away_counts,
            self.diff_values,
            self.total_objective,
            self.pair_to_week  
        ) = create_sts_model_MinMax(
            n,
            self.exactly_one_encoding,
            self.at_most_k_encoding
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
            print(f"\n--- Optimization started for n={self.n} ---")
            print(f"  Using encodings: {self.exactly_one_encoding.__name__}, {self.at_most_k_encoding.__name__}")

        while True:
            current_elapsed_time = time.time() - init_time
            remaining_time = math.floor(timeout_timestamp - time.time())

            if remaining_time <= 0:
                if verbose:
                    print("  Global timeout reached.")
                break

            self.solver.push()
            self.solver.set("timeout", remaining_time * 1000)

            if optimal_objective_value is not None:
                self.solver.add(self.total_objective < optimal_objective_value)
                if verbose:
                    print(f"  Looking for solution with total diff < {optimal_objective_value} (Remaining time: {remaining_time}s)...")
            else:
                if verbose:
                    print(f"  Looking for initial solution (Remaining time: {remaining_time}s)...")

            status = self.solver.check()
            current_elapsed_time = time.time() - init_time

            if verbose:
                print(f"  Solver iteration result: {status} (Elapsed time: {current_elapsed_time:.2f}s)")

            if status == sat:
                model = self.solver.model()
                current_objective = model.evaluate(self.total_objective).as_long()
                solution_found_at_least_once = True

                if verbose:
                    print(f"    Found solution with total_diff = {current_objective}")

                if optimal_objective_value is None or current_objective < optimal_objective_value:
                    optimal_objective_value = current_objective
                    best_solution_schedule = []

                    for (i, j, p), var in self.match_period_vars.items():
                        if model.evaluate(var):
                            home_team = i if model.evaluate(self.home_vars[(i, j)]) else j
                            away_team = j if model.evaluate(self.home_vars[(i, j)]) else i
                            week = self.pair_to_week[(i, j)] + 1  # weeks start from 0
                            best_solution_schedule.append((home_team + 1, away_team + 1, week, p + 1))

                    if verbose:
                        print("    Home/Away counts for this solution:")
                        for t in range(self.NUM_TEAMS):
                            h = model.evaluate(self.home_counts[t]).as_long()
                            a = model.evaluate(self.away_counts[t]).as_long()
                            d = model.evaluate(self.diff_values[t]).as_long()
                            print(f"      Team {t+1}: Home = {h}, Away = {a}, Diff = {d}")

                    if optimal_objective_value == 1:
                        proven_optimal_final = True
                        if verbose:
                            print(f"    Lower bound ({self.n}) reached. Optimization complete.")
                        self.solver.pop()
                        break

                self.solver.pop()

            elif status == unsat:
                proven_optimal_final = True
                if verbose:
                    print("  No better solution found (UNSAT). Optimization complete.")
                self.solver.pop()
                break

            elif status == unknown:
                if verbose:
                    print(f"  Solver returned 'unknown' (likely timeout within iteration).")
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
            print(f"  Final objective: {optimal_objective_value}")
            print(f"  Proven optimal: {proven_optimal_final}")
            print("  Final solver statistics:")
            for k, v in final_stats.items():
                print(f"    {k}: {v}")

        if proven_optimal_final:
            return (optimal_objective_value, best_solution_schedule, True,
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
            
            
            

'''
from z3 import *
import time
import math
from create_model_MinMax import create_sts_model_MinMax
from encoding_utils import heule_exactly_one, at_most_k_seq

# Light model and advanced encodings
# Use of different optimization function: Min(Max(Diff))
# Use of Symmetry Breaking constraints 

class STS_Different_Optimized_Model:
    def __init__(self, n, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding
        

        self.solver, self.match_vars, self.home_vars, self.home_counts, self.away_counts, self.diff_values, self.total_objective = create_sts_model_MinMax(
            n, 
            self.exactly_one_encoding, 
            self.at_most_k_encoding,
            symmetry_breaking=True 
        )
        
        
    def solve(self, timeout_seconds, random_seed=None, verbose=False, solver_options=True):
        if solver_options:
            if random_seed is not None:
                self.solver.set("random_seed", random_seed)
            
            if(self.n <= 6):
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
            print(f"\n--- Optimization started for n={self.n} ---")
            print(f"  Using exactly_one: {self.exactly_one_encoding.__name__}, at_most_k: {self.at_most_k_encoding.__name__}")
        
        while True:
            current_elapsed_time = time.time() - init_time
            remaining_time = math.floor(timeout_timestamp - time.time())
            
            if remaining_time <= 0:
                if verbose:
                    print("  Global timeout reached. Terminating optimization loop.")
                break 

            self.solver.push() 
            self.solver.set("timeout", remaining_time * 1000) 

            if optimal_objective_value is not None:
                self.solver.add(self.total_objective < optimal_objective_value)
                if verbose:
                    print(f"  Searching for a solution with total diff < {optimal_objective_value} (Remaining time: {remaining_time}s)...")
            else:
                if verbose:
                    print(f"  Searching for initial solution (Remaining time: {remaining_time}s)...")

            status = self.solver.check()
            current_elapsed_time = time.time() - init_time
            
            if verbose:
                print(f"  Solver iteration result: {status} (Elapsed time: {current_elapsed_time:.2f}s)")

            if status == sat:
                model = self.solver.model()
                current_objective = model.evaluate(self.total_objective).as_long()
                solution_found_at_least_once = True 
                
                if verbose:
                    print(f"    Found solution with total diff = {current_objective}")
                
                if optimal_objective_value is None or current_objective < optimal_objective_value:
                    optimal_objective_value = current_objective
                    if verbose:
                        print(f"    New best total diff found: {optimal_objective_value}")

                    best_solution_schedule = []
                    for w in range(self.NUM_WEEKS):
                        for p in range(self.NUM_PERIODS_PER_WEEK):
                            for i in range(self.NUM_TEAMS):
                                for j in range(i + 1, self.NUM_TEAMS):
                                    m_var = self.match_vars[(i, j, w, p)]
                                    if model.evaluate(m_var):
                                        if model.evaluate(self.home_vars[(i, j)]):
                                            best_solution_schedule.append((i + 1, j + 1, w + 1, p + 1))
                                        else:
                                            best_solution_schedule.append((j + 1, i + 1, w + 1, p + 1))
                    
                    if verbose:
                        print("    Home/Away counts for this solution:")
                        for i in range(self.NUM_TEAMS):
                            h_count = model.evaluate(self.home_counts[i]).as_long()
                            a_count = model.evaluate(self.away_counts[i]).as_long()
                            d_val = model.evaluate(self.diff_values[i]).as_long()
                            calculated_diff = abs(h_count - a_count) 
                            print(f"      Team {i+1}: Home = {h_count}, Away = {a_count}, Diff = {d_val} (Calcolata: {calculated_diff})")

                    
                    if optimal_objective_value == 1: 
                        proven_optimal_final = True 
                        if verbose:
                            print(f"    Lower bound ({self.n}) reached. Optimization complete.")
                        self.solver.pop() 
                        break 

                self.solver.pop() 

            elif status == unsat:
                proven_optimal_final = True 
                if verbose:
                    print("  No better solution found (UNSAT). Optimization complete.")
                self.solver.pop() 
                break

            elif status == unknown:
                if verbose:
                    print(f"  Solver returned 'unknown' (likely timeout within iteration).")
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
            print(f"  Final objective: {optimal_objective_value}")
            print(f"  Proven optimal: {proven_optimal_final}")
            print("  Final solver statistics:")
            for k, v in final_stats.items():
                print(f"    {k}: {v}")

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
'''