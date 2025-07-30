from z3 import *
import time
import math
from create_model_MinSum import create_sts_model_MinSum
from encoding_utils import heule_exactly_one, at_most_k_seq


class STS_Optimized_Decisional:
    def __init__(self, n, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
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
        ) = create_sts_model_MinSum(
            n,
            self.exactly_one_encoding,
            self.at_most_k_encoding,
            symmetry_breaking=True
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
        
        init_time = time.time()
        self.solver.set("timeout", timeout_seconds * 1000)

        if verbose:
            print(f"--- SAT solving (decision only) for n={self.n} ---")

        status = self.solver.check()
        elapsed = time.time() - init_time
        
        

        stat = self.solver.statistics()
        final_stats = {
            'restarts': stat.get_key_value('restarts') if 'restarts' in stat.keys() else 0,
            'max_memory': stat.get_key_value('max memory') if 'max memory' in stat.keys() else 0,
            'mk_bool_var': stat.get_key_value('mk bool var') if 'mk bool var' in stat.keys() else 0,
            'conflicts': stat.get_key_value('conflicts') if 'conflicts' in stat.keys() else 0,
            'solve_time': elapsed
        }

        if verbose:
            print(f"Status: {status}, Time: {elapsed:.2f}s")

        
        if status == sat:
            model = self.solver.model()
            best_solution_schedule = []
            for (i, j, p), var in self.match_period_vars.items():
                if model.evaluate(var):
                    home_team = i if model.evaluate(self.home_vars[(i, j)]) else j
                    away_team = j if model.evaluate(self.home_vars[(i, j)]) else i
                    week = self.pair_to_week[(i, j)] + 1  # +1 per week "umana"
                    best_solution_schedule.append((home_team + 1, away_team + 1, week, p + 1))
                            
            return (None, best_solution_schedule, True,
                        final_stats['solve_time'], final_stats['restarts'],
                        final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
        
        else:
            return (None, None, True,
                    final_stats['solve_time'], final_stats['restarts'],
                    final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])


'''
class STS_Optimized_Decisional:
    def __init__(self, n, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding
        
        self.solver, self.match_vars, self.home_vars, self.home_counts, self.away_counts, self.diff_values, self.total_objective = create_sts_model_MinSum(
            n, 
            self.exactly_one_encoding, 
            self.at_most_k_encoding,
            symmetry_breaking=True
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
        
        init_time = time.time()
        self.solver.set("timeout", timeout_seconds * 1000)

        if verbose:
            print(f"--- SAT solving (decision only) for n={self.n} ---")

        status = self.solver.check()
        elapsed = time.time() - init_time
        
        

        stat = self.solver.statistics()
        final_stats = {
            'restarts': stat.get_key_value('restarts') if 'restarts' in stat.keys() else 0,
            'max_memory': stat.get_key_value('max memory') if 'max memory' in stat.keys() else 0,
            'mk_bool_var': stat.get_key_value('mk bool var') if 'mk bool var' in stat.keys() else 0,
            'conflicts': stat.get_key_value('conflicts') if 'conflicts' in stat.keys() else 0,
            'solve_time': elapsed
        }

        if verbose:
            print(f"Status: {status}, Time: {elapsed:.2f}s")

        
        if status == sat:
            model = self.solver.model()
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
        
            return (None, best_solution_schedule, True,
                        final_stats['solve_time'], final_stats['restarts'],
                        final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
        
        else:
            return (None, None, True,
                    final_stats['solve_time'], final_stats['restarts'],
                    final_stats['max_memory'], final_stats['mk_bool_var'], final_stats['conflicts'])
'''