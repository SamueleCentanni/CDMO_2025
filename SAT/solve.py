# SOLVER DI NOXIA SU GITHUB
import time
import multiprocessing
import logging
import traceback
from functools import partial # serve per precompilare una funzione o classe con alcuni argomenti già fissati in anticipo
from encoding_utils import exactly_one_np, at_most_k_np, heule_exactly_one, at_most_k_seq
from inutilities.opt_base import STS_Optimized_Model
from inutilities.opt_sb import STS_Optimized_Model_SB
from inutilities.opt_sb_encoding import STS_Optimized_Model_SB_Encodings
from inutilities.opt_sb_enc_solver import STS_Optimized_Model_SB_Solver
from inutilities.opt_sb_heule import STS_Optimized_Model_SB_Heule
from inutilities.opt_sb_heule_2 import STS_Optimized_Model_SB_Heule_2
from opt_sb_heule_3 import STS_Optimized_Model_SB_Heule_3
logger = logging.getLogger(__name__)


def modelRunner(ModelClass, instance, timeout, random_seed, queue):
    objective = None
    solution = None
    optimality = False
    solve_time = timeout

    try:
        start_model_init = time.time()

        def_model = ModelClass(instance)
        model_init_time = round(time.time() - start_model_init)
        logger.info(f"Model created")
        
        objective, solution, optimality, solve_time, restart, max_memory, mk_bool_var, conflicts = def_model.solve(timeout-model_init_time, random_seed)
        solve_time = solve_time + model_init_time
    except Exception as e:
        logger.error(f"Exception {e}")
        print(traceback.format_exc())

    result = {}

    if objective is not None:
        result = {
            'obj': objective,
            'sol': solution,
            'optimal': optimality,
            'time': solve_time,
            'restart' : restart,
            'max_memory': max_memory,
            'mk_bool_var': mk_bool_var,
            'conflicts': conflicts
        }
    else:
        result = {
            'obj': None,
            'sol': None,
            'optimal': False,
            'time': timeout,
            'restart' : None,
            'max_memory': None,
            'mk_bool_var': None,
            'conflicts': None
        }
    queue.put(result, block=False)


def solve(instance, instance_number, timeout, cache={}, random_seed=42, models_filter=None, **kwargs):
    
    models = {
        #'base-bw-seq': STS_Optimized_Model,
        #'sb-bw-seq': STS_Optimized_Model_SB,
        #'sb-seq-seq': STS_Optimized_Model_SB_Encodings,
        #'sb-seq-seq-solver': STS_Optimized_Model_SB_Solver,
        #'sb-heule-seq-solver': STS_Optimized_Model_SB_Heule,
        #'sb-heule-seq-solver2':STS_Optimized_Model_SB_Heule_2,
        'sb-heule-seq-solver3': STS_Optimized_Model_SB_Heule_3,
    }

    results = {}

    for model in models.keys():
        if (models_filter is not None) and (model not in models_filter):
            continue
        logger.info(f"Starting model {model}")

        # Check if result is in cache
        if model in cache:
            logger.info(f"Cache hit")
            results[model] = cache[model]
            continue
        
        res = None
        runner_queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=modelRunner, args=(models[model], instance, timeout, random_seed, runner_queue))
        try:
            proc.start()
            res = runner_queue.get(block=True, timeout=timeout+1) # Tolerance to wait for Z3 timeout
        except Exception as e:
            print(traceback.format_exc())
            logger.error(f"Exception {e}")
        finally:
            proc.terminate()

        if res is None:
            results[model] = {
                'obj': None,
                'sol': None,
                'optimal': False,
                'time': timeout,
                'restart' : None,
                'max_memory': None,
                'mk_bool_var': None,
                'conflicts': None
            }
        else:
            results[model] = res
    print(f"\n{results}")

    return results