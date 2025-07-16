# UTILIZZO DI OPTIMIZER AL POSTO DI SOLVER

from z3 import *
import time
from create_model import create_sts_model
from encoding_utils import heule_exactly_one, at_most_k_seq

class STS_Optimized_Model_SB_Heule_Optimize:
    def __init__(self, n, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding

        # Usiamo Optimize() invece di Solver()
        self.optimizer = Optimize()
        
        # Crea modello con i vincoli
        (model_optimizer, self.games_vars, self.home_counts, 
         self.away_counts, self.diff_values, self.total_objective) = create_sts_model(
            n, self.exactly_one_encoding, self.at_most_k_encoding, 
            symmetry_breaking=True, custom_solver=self.optimizer)

        # Imposta obiettivo di minimizzazione
        self.optimizer.minimize(self.total_objective)

    def solve(self, timeout_seconds, random_seed=None):
        if random_seed is not None:
            set_param("sat.random_seed", random_seed)

        self.optimizer.set("timeout", timeout_seconds * 1000)
        init_time = time.time()
        
        print(f"\n--- Starting Optimize() for n={self.n} ---")
        print(f"  Using exactly_one: {self.exactly_one_encoding.__name__}, at_most_k: {self.at_most_k_encoding.__name__}")

        status = self.optimizer.check()
        elapsed = time.time() - init_time

        if status == sat:
            model = self.optimizer.model()
            optimal_objective = model.evaluate(self.total_objective).as_long()
            print(f"  Optimal solution found with total difference = {optimal_objective}")

            best_solution_schedule = []
            for (i, j, w, p), var in self.games_vars.items():
                if model.evaluate(var, model_completion=True):
                    best_solution_schedule.append((i+1, j+1, w+1, p+1))

            print("    Home/Away counts for this solution:")
            for i in range(self.NUM_TEAMS):
                h = model.evaluate(self.home_counts[i]).as_long()
                a = model.evaluate(self.away_counts[i]).as_long()
                d = model.evaluate(self.diff_values[i]).as_long()
                print(f"      Team {i+1}: Home = {h}, Away = {a}, Diff = {d}")

            stats = self.optimizer.statistics()
            final_stats = {
                'restarts': stats.get_key_value('restarts') if 'restarts' in stats.keys() else 0,
                'max_memory': stats.get_key_value('max memory') if 'max memory' in stats.keys() else 0,
                'mk_bool_var': stats.get_key_value('mk bool var') if 'mk bool var' in stats.keys() else 0,
                'conflicts': stats.get_key_value('conflicts') if 'conflicts' in stats.keys() else 0,
                'solve_time': elapsed
            }

            return (optimal_objective, best_solution_schedule, True, 
                    final_stats['solve_time'], final_stats['restarts'], 
                    final_stats['max_memory'], final_stats['mk_bool_var'], 
                    final_stats['conflicts'])
        else:
            print(f"  No solution found. Status: {status}")
            stats = self.optimizer.statistics()
            return (None, None, False, time.time() - init_time,
                    stats.get_key_value('restarts') if 'restarts' in stats.keys() else 0,
                    stats.get_key_value('max memory') if 'max memory' in stats.keys() else 0,
                    stats.get_key_value('mk bool var') if 'mk bool var' in stats.keys() else 0,
                    stats.get_key_value('conflicts') if 'conflicts' in stats.keys() else 0)