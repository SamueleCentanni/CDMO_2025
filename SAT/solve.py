import time
import multiprocessing
import traceback

from heule_seq_matrix import STS_Optimized_Matrix
from np_np_optimization import STS_Optimized_BaseModel
from heule_seq_light import STS_Optimized_LightModel
from heule_seq_diff_opt import STS_Different_Optimized_Model
from heule_seq_light_NoSB import STS_Optimized_LightModel_NoSB
from heule_seq_decisional import STS_Optimized_Decisional


def modelRunner(ModelClass, instance, timeout, random_seed, queue, verbose):
    objective = None
    solution = None
    optimality = False
    solve_time = timeout

    try:
        start_model_init = time.time()

        def_model = ModelClass(instance)
        model_init_time = round(time.time() - start_model_init)
        if verbose:
            print(f"Model created in {model_init_time}s")

        objective, solution, optimality, solve_time, restart, max_memory, mk_bool_var, conflicts = def_model.solve(timeout - model_init_time, random_seed=random_seed, verbose=verbose)
        solve_time += model_init_time

    except Exception as e:
        if verbose:
            print(f"Exception occurred during model execution: {e}")
            print(traceback.format_exc())
        queue.put((False, None))
        return

    result = {}

    if objective is not None or optimality:
        result = {
            'obj': objective,
            'sol': solution,
            'optimal': optimality,
            'time': solve_time,
            'restart': restart,
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
            'restart': None,
            'max_memory': None,
            'mk_bool_var': None,
            'conflicts': None
        }
    queue.put(result, block=False)


def solve(instance, timeout, cache={}, random_seed=42, models_filter=None, verbose=False, **kwargs):
    
    models = {
        'sb-np-np-std-opt': STS_Optimized_BaseModel,
        'heule-seq-model-matrix-std-opt': STS_Optimized_Matrix,
        'heule-seq-model-light-std-opt-NO-SB': STS_Optimized_LightModel_NoSB,
        'heule-seq-model-light-std-opt-SB': STS_Optimized_LightModel,
        'sb-heule-seq-diff-opt': STS_Different_Optimized_Model,
        'sb-heule-seq-decisional': STS_Optimized_Decisional,
    }

    results = {}

    for model in models.keys():
        if (models_filter is not None) and (model not in models_filter):
            continue
        if verbose:
            print(f"\nStarting model: {model}")

        # Check if result is in cache
        if model in cache:
            if verbose:
                print(f"Cache hit for model: {model}")
            results[model] = cache[model]
            continue
        
        res = None
        runner_queue = multiprocessing.Queue()
        proc = multiprocessing.Process(target=modelRunner, args=(models[model], instance, timeout, random_seed, runner_queue, verbose))
        try:
            proc.start()
            res = runner_queue.get(block=True, timeout=timeout + 1)  # Extra second for tolerance
        except Exception as e:
            if verbose:
                print(f"Exception occurred during process execution: {e}")
                print(traceback.format_exc())
        finally:
            proc.terminate()

        if res is None:
            results[model] = {
                'obj': None,
                'sol': None,
                'optimal': False,
                'time': timeout,
                'restart': None,
                'max_memory': None,
                'mk_bool_var': None,
                'conflicts': None
            }
        else:
            results[model] = res

    print(f"\n{results}")
    return results