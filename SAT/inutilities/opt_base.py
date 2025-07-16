from z3 import *
import time
import math
from create_model import create_sts_model
from encoding_utils import heule_exactly_one, exactly_k_np, exactly_one_seq, exactly_one_bw, exactly_one_np, at_most_k_np, at_most_k_seq
from create_model_2 import create_sts_model_compact

# Model base, no symmetry breaking and standard encoding (naive)
class STS_Optimized_Model:
    def __init__(self, n, exactly_one_encoding=exactly_one_bw, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding
        
        # in this way i can change the encodings as i prefer
        self.solver, self.games_vars, self.home_counts, self.away_counts, self.diff_values, self.total_objective = create_sts_model(n, 
                                                                                                                                self.exactly_one_encoding, 
                                                                                                                                self.at_most_k_encoding,
                                                                                                                                )

        
    def solve(self, timeout_seconds, random_seed=None):
        set_option("sat.local_search", True) 
        if random_seed is not None:
            self.solver.set("random_seed", random_seed)
            

        # Init for iterative optimization
        optimal_objective_value = None
        best_solution_schedule = []
        init_time = time.time()
        timeout_timestamp = init_time + timeout_seconds

        print(f"\n--- Starting Optimization for n={self.n} ---")
        print(f"  Using exactly_one: {self.exactly_one_encoding.__name__}, at_most_k: {self.at_most_k_encoding.__name__}")

        while True:
            remaining_time = math.floor(timeout_timestamp - time.time())
            if remaining_time <= 0:
                print("  Overall timeout reached. Breaking optimization loop.")
                break # Overall timeout for the solve method

            self.solver.set("timeout", remaining_time * 1000) 
            self.solver.push() 

            # constraint to find a strictly better solution
            if optimal_objective_value is not None:
                self.solver.add(self.total_objective < optimal_objective_value)
                print(f"  Searching for solution with total difference < {optimal_objective_value} (Remaining overall time: {remaining_time}s)...")
            else:
                print(f"  Searching for initial solution (Remaining overall time: {remaining_time}s)...")

            status = self.solver.check()
            current_elapsed_time = time.time() - init_time
            
            print(f"  Solver iteration returned: {status} (Elapsed: {current_elapsed_time:.2f}s)")

            if status == sat:
                model = self.solver.model()
                current_objective = model.evaluate(self.total_objective).as_long()
                
                print(f"    Found solution with total difference = {current_objective}")
                
                if optimal_objective_value is None or current_objective < optimal_objective_value:
                    optimal_objective_value = current_objective
                    print(f"    New best total difference found: {optimal_objective_value}")

                    best_solution_schedule = []
                    for (i, j, w, p), var in self.games_vars.items():
                        if model.evaluate(var):
                            best_solution_schedule.append((i+1, j+1, w+1, p+1))
                    
                    print("    Home/Away counts for this solution:")
                    for i in range(self.NUM_TEAMS):
                        h_count = model.evaluate(self.home_counts[i]).as_long()
                        a_count = model.evaluate(self.away_counts[i]).as_long()
                        d_val = model.evaluate(self.diff_values[i]).as_long()
                        calculated_diff = abs(h_count - a_count)
                        print(f"      Team {i+1}: Home = {h_count}, Away = {a_count}, Diff = {d_val} (Calculated: {calculated_diff})")

                else:
                    print("    Found solution, but it's not strictly better than the current best. Optimization complete.")
                    self.solver.pop() # Pop the last constraint to revert
                    break # Exit loop as no better solution found

            elif status == unsat:
                print("  No better solution found. Optimization complete.")
                self.solver.pop() # Pop the last constraint that made it unsat
                break

            elif status == unknown:
                print(f"  Solver returned 'unknown' (likely timeout within iteration).")
                break # Cannot guarantee optimality, so stop

            self.solver.pop() # Remove the specific objective constraint for the last iteration
            # Loop continues to search for better solution (if 'sat' was returned)

        stat = self.solver.statistics()
        final_stats = {
            'restarts': stat.get_key_value('restarts') if 'restarts' in stat.keys() else 0,
            'max_memory': stat.get_key_value('max memory') if 'max memory' in stat.keys() else 0,
            'mk_bool_var': stat.get_key_value('mk bool var') if 'mk bool var' in stat.keys() else 0,
            'conflicts': stat.get_key_value('conflicts') if 'conflicts' in stat.keys() else 0,
            'solve_time': current_elapsed_time # Total time for optimization
        }
        
        print("\n--- Optimization Finished ---")
        print(f"  Optimal Total Difference found: {optimal_objective_value}")
        print("  Final Solver Statistics (from last check):")
        for k, v in final_stats.items():
            print(f"    {k}: {v}")


        if best_solution_schedule:
            print(f"  Number of active matches in best solution: {len(best_solution_schedule)}")
            return (optimal_objective_value,               # objective
                    best_solution_schedule,                # solution
                    True,                                  # optimality (True = found a solution, not necessarily optimal)
                    final_stats['solve_time'],             # solve_time
                    final_stats['restarts'],               # restart
                    final_stats['max_memory'],             # max_memory
                    final_stats['mk_bool_var'],            # mk_bool_var
                    final_stats['conflicts'])              # conflicts
        else:
            print("  No solution found at all.")
            return (None,                                  # objective
                    None,                                  # solution
                    False,                                 # optimality
                    final_stats['solve_time'],             # solve_time
                    final_stats['restarts'],               # restart
                    final_stats['max_memory'],             # max_memory
                    final_stats['mk_bool_var'],            # mk_bool_var
                    final_stats['conflicts'])              # conflicts

