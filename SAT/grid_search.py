from inutilities.opt_sb_heule_3_gs import STS_Optimized_Model_SB_Heule_3
from encoding_utils import at_most_k_seq

def grid_search(n, model_class=STS_Optimized_Model_SB_Heule_3, at_most_k_encoding=at_most_k_seq):
    phase_selection = [0, 2,]
    restart_factor = [ 1.2, 1.5,]
    restart_strategy = [1, 2]
    
    results = []
    statistics = {
        'phase_selection': None,
        'restart_factor': None,
        'restart_strategy': None,
        'optimal_objective_value': None,
        'time': None,
        'optimality': None,
        }
    
    
    
    for ps in phase_selection:
        for rf in restart_factor:
            for rs in restart_strategy:
                sts_model = model_class(n, ps=ps, rf=rf, rs=rs, at_most_k_encoding=at_most_k_encoding)
                (objective, solution, optimality, solve_time, values) = sts_model.solve(timeout_seconds=60, random_seed=42)
                (ps_value,rf_value,rs_value) = values
                
                statistics = {
                                'phase_selection': ps_value,
                                'restart_factor': rf_value,
                                'restart_strategy': rs_value,
                                'optimal_objective_value': objective,
                                'time': solve_time,
                                'optimality': optimality,
                            }
                
                results.append(statistics)
    
    print(results)