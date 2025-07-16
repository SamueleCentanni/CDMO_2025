# GRID SEARCH

from z3 import *
import time
import math
from create_model import create_sts_model
from create_model_2 import create_sts_model_compact
from create_model_3 import create_sts_model_compact_optimized 
from encoding_utils import heule_exactly_one, exactly_k_np, exactly_one_seq, exactly_one_bw, exactly_one_np, at_most_k_np, at_most_k_seq

# With SYMMETRY BREAKING SB and best encoding (heule + sequential)
class STS_Optimized_Model_SB_Heule_3:
    def __init__(self, n, ps, rf, rs, exactly_one_encoding=heule_exactly_one, at_most_k_encoding=at_most_k_seq):
        self.n = n
        self.NUM_TEAMS = n
        self.NUM_WEEKS = self.NUM_TEAMS - 1
        self.NUM_PERIODS_PER_WEEK = self.n // 2
        self.exactly_one_encoding = exactly_one_encoding
        self.at_most_k_encoding = at_most_k_encoding
        
        self.ps = ps
        self.rf = rf
        self.rs = rs
            
        self.solver, self.match_vars, self.home_vars, self.home_counts, self.away_counts, self.diff_values, self.total_objective = create_sts_model_compact_optimized(n, 
                                                                                                                                self.exactly_one_encoding, 
                                                                                                                                self.at_most_k_encoding,
                                                                                                                                symmetry_breaking=True)
        
    def solve(self, timeout_seconds, random_seed=None):
        set_option("sat.local_search", True) 
        if random_seed is not None:
            self.solver.set("random_seed", random_seed)
        
        if(self.n <= 8):
            self.solver.set("phase_selection", 0)
            self.solver.set("restart_strategy", 0)
        else:
            self.solver.set("phase_selection", self.ps) # da 2 a 0
            self.solver.set("restart_factor", self.rf) # da 1.2 a 1.5
            self.solver.set("restart_strategy", self.rs) # da 1 a 2
    
        optimal_objective_value = None 
        best_solution_schedule = []    
        
        init_time = time.time()
        timeout_timestamp = init_time + timeout_seconds

        proven_optimal_final = False 
        solution_found_at_least_once = False 

        print(f"\n--- Avvio Ottimizzazione per n={self.n} ---")
        print(f"  Utilizzo exactly_one: {self.exactly_one_encoding.__name__}, at_most_k: {self.at_most_k_encoding.__name__}")
        
        while True:
            current_elapsed_time = time.time() - init_time
            remaining_time = math.floor(timeout_timestamp - time.time())
            
            if remaining_time <= 0:
                print("  Timeout globale raggiunto. Interruzione del loop di ottimizzazione.")
                break 

            self.solver.push() 
            self.solver.set("timeout", remaining_time * 1000) 

            if optimal_objective_value is not None:
                self.solver.add(self.total_objective < optimal_objective_value)
                print(f"  Ricerca soluzione con differenza totale < {optimal_objective_value} (Tempo rimanente complessivo: {remaining_time}s)...")
            else:
                print(f"  Ricerca soluzione iniziale (Tempo rimanente complessivo: {remaining_time}s)...")

            status = self.solver.check()
            current_elapsed_time = time.time() - init_time
            
            print(f"  L'iterazione del solver ha restituito: {status} (Tempo trascorso: {current_elapsed_time:.2f}s)")

            if status == sat:
                model = self.solver.model()
                current_objective = model.evaluate(self.total_objective).as_long()
                solution_found_at_least_once = True 
                
                print(f"    Trovata soluzione con differenza totale = {current_objective}")
                
                if optimal_objective_value is None or current_objective < optimal_objective_value:
                    optimal_objective_value = current_objective
                    print(f"    Nuova migliore differenza totale trovata: {optimal_objective_value}")

                    best_solution_schedule = []
                    for (i, j, w, p), m_var in self.match_vars.items(): 
                        if model.evaluate(m_var): 
                            if model.evaluate(self.home_vars[(i,j)]):
                                best_solution_schedule.append((i+1, j+1, w+1, p+1)) 
                            else: 
                                best_solution_schedule.append((j+1, i+1, w+1, p+1))
                    
                    print("    Home/Away counts for this solution:")
                    for i in range(self.NUM_TEAMS):
                        h_count = model.evaluate(self.home_counts[i]).as_long()
                        a_count = model.evaluate(self.away_counts[i]).as_long()
                        d_val = model.evaluate(self.diff_values[i]).as_long()
                        calculated_diff = abs(h_count - a_count) 
                        print(f"      Team {i+1}: Home = {h_count}, Away = {a_count}, Diff = {d_val} (Calcolata: {calculated_diff})")

                    # CONTROLLO AGGIORNATO PER IL LOWER BOUND N
                    if optimal_objective_value == self.n: 
                        proven_optimal_final = True 
                        print(f"    Lower bound ({self.n}) raggiunto. Ottimizzazione completa.")
                        self.solver.pop() 
                        break 

                self.solver.pop() 

            elif status == unsat:
                proven_optimal_final = True 
                print("  Nessuna soluzione migliore trovata (UNSAT). Ottimizzazione completa.")
                self.solver.pop() 
                break

            elif status == unknown:
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
        
        print("\n--- Ottimizzazione Terminata ---")
        print(f"  Obiettivo finale: {optimal_objective_value}")
        print(f"  Ottimalità Provata: {proven_optimal_final}")
        print("  Statistiche finali del Solver:")
        for k, v in final_stats.items():
            print(f"    {k}: {v}")

        if proven_optimal_final: 
            if optimal_objective_value is not None:
                return (optimal_objective_value, best_solution_schedule, True,
                        final_stats['solve_time'],(self.ps, self.rf, self.rs))

            else:
                print("  Problema provato essere infattibile (UNSAT).")
                return (None, None, True, 
                        final_stats['solve_time'],(self.ps, self.rf, self.rs))
        elif solution_found_at_least_once:
            return (optimal_objective_value, best_solution_schedule, False,
                    final_stats['solve_time'], (self.ps, self.rf, self.rs))
        else:
            print("  Nessuna soluzione trovata del tutto (timeout o stato sconosciuto prima di qualsiasi SAT).")
            return (None, None, False,
                    final_stats['solve_time'], (self.ps, self.rf, self.rs))