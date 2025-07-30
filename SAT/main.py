from z3 import *
from utils import print_weekly_schedule
import argparse
from different_solvers import solve_sts_with_dimacs

from utils import save_results_as_json
from utils import save_stats_as_json
from utils import save_compare_solver_result

from encoding_utils import heule_exactly_one, at_most_k_seq
from create_model_MinSum import create_sts_model_MinSum

from solve import solve 

from functools import partial


# === DIMACS-mode solvers ===
# The user can try different solver using only the MinSum function and heule_exactly_one, at_most_k_seq encodings
# No optimization, only decisional
def model_creator_wrapper(n_teams, exactly_one_encoding, at_most_k_encoding):
    return create_sts_model_MinSum(
        n_teams,
        exactly_one_encoding,
        at_most_k_encoding,
        symmetry_breaking=True
    )


def different_scheduler(n_teams, exactly_one_encoding, at_most_k_encoding, solver, timeout, verbose):
    model_creator = partial(
        model_creator_wrapper,
        n_teams=n_teams,
        exactly_one_encoding=exactly_one_encoding,
        at_most_k_encoding=at_most_k_encoding
    )

    result = solve_sts_with_dimacs(
        model_creator_fn=model_creator,
        timeout=timeout,
        solver_name=solver
    )   

    if verbose:
        if result["satisfiable"]:
            print_weekly_schedule(result['sol'], num_teams=n_teams)
        else:
            print("UNSAT or TIMEOUT")
        
    # COMPARING DIFFERENT SOLVERS IN DECISIONAL VERSION
    save_compare_solver_result(n=n_teams, solver_name=solver, result=result)

# === Solver-mode ===
def solver(n_teams, models_filter, verbose=False, timeout=300, save_files=False, save_stats=False):
    results = solve(
        instance=n_teams,
        models_filter=models_filter,
        timeout=timeout,
        random_seed=42,
        verbose=verbose
    )

    if verbose:
        for model_name, result in results.items():
            print(f"\n--- {model_name} ---")
            print(f"Objective: {result['obj']}")
            print(f"Optimal: {result['optimal']}")
            print(f"Time: {result['time']}s")
            print(f"Solution: {result['sol']}")
            print_weekly_schedule(result['sol'], num_teams=n_teams)

    if save_files:
        if verbose:
            print("\nSaving on json file\n")
        save_results_as_json(n=n_teams, results=results)
    
    if save_stats:
        save_stats_as_json(n=n_teams, results=results)
    
    #for model_name, result in results.items():
    #    save_compare_solver_result(n=n_teams, solver_name=model_name, result=result)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run STS model in various modes.")
    parser.add_argument('mode', choices=['optimization', 'dimacs', 'decisional'], default='optimization',
                        help="Execution mode: 'optimization', 'decisional' or 'dimacs'. Default is 'optimization'")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--n_range', type=str, help="Range of number of teams, e.g., --n_range 6-12")
    group.add_argument('--n', type=int, nargs='+', help="List of even team counts, e.g., --n 6 8 10")

    parser.add_argument('--timeout', type=int, help="Set timeout in seconds", default=300)
    parser.add_argument('--verbose', action='store_true', help="Print detailed output")

    parser.add_argument('--models', nargs='+', choices=['light_SB', 'light_NoSB', 'diff', 'matrix', 'base_naive', 'all'],
                        help="List of models to run (e.g., --models light_SB matrix)", default=['all'])

    parser.add_argument('--solvers', nargs='+', choices=['glucose4', 'glucose3', 'minisat', 'all'], default=['all'],
                        help="SAT solvers to use in dimacs mode")
    
    parser.add_argument('--save_json', action='store_true', help="Save solver results on json files")

    args = parser.parse_args()

    # Parse team counts
    if args.n_range:
        try:
            start_n, end_n = map(int, args.n_range.split('-'))
            if start_n % 2 != 0 or end_n % 2 != 0:
                raise ValueError("Both start and end must be even numbers.")
            if start_n <= 0 or end_n <= 0:
                raise ValueError("Both numbers must be positive.")
            ns = list(range(start_n, end_n + 1, 2))
        except Exception as e:
            print(f"Invalid range format: {args.n_range}")
            print("Use format like '6-12', with even numbers.")
            exit(1)
    elif args.n:
        if not all(n > 0 and n % 2 == 0 for n in args.n):
            print("All --n values must be positive even numbers.")
            exit(1)
        ns = args.n
    else:
        ns = []

    # Map input_names <-> models
    model_name_map = {
        'light_SB': 'heule-seq-model-light-std-opt-SB',
        'light_NoSB': 'heule-seq-model-light-std-opt-NO-SB',
        'diff': 'sb-heule-seq-diff-opt',
        'matrix': 'heule-seq-model-matrix-std-opt',
        'base_naive': 'sb-np-np-std-opt',
    }

    

    timeout = args.timeout
    verbose = args.verbose

    for n in ns:
        print(f"\n{'='*30}\nRunning for N={n} teams\n{'='*30}")
        
        if args.mode == 'optimization':
            if 'all' in args.models:
                selected_models = list(model_name_map.values())
            else:
                try:
                    selected_models = [model_name_map[m] for m in args.models]
                except KeyError as e:
                    print(f"Unknown model: {e}")
                    exit(1)
                    
            solver(n_teams=n,
                   verbose=verbose,
                   timeout=timeout,
                   models_filter=selected_models,
                   save_files=args.save_json)
            
        elif args.mode == 'decisional':
            solver(n_teams=n,
                   verbose=verbose,
                   timeout=timeout,
                   models_filter='sb-heule-seq-decisional',
                   )
        
        elif args.mode == 'dimacs':
            exactly_one_encoding = heule_exactly_one
            at_most_k_encoding = at_most_k_seq
            if 'all' in args.solvers:
                solvers_list = ['glucose4', 'minisat', 'glucose3']
            else:
                solvers_list = args.solvers
            for s in solvers_list:
                print(f"\n--- Solving with {s} ---")
                different_scheduler(n,
                                    exactly_one_encoding,
                                    at_most_k_encoding,
                                    solver=s,
                                    timeout=timeout,
                                    verbose=verbose)