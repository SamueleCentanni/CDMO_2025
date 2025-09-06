import os
import argparse
import sys
from typing import Set, List
import subprocess

def parse_n_teams(n_input: str) -> List[int]:
    """
    Parses the input for -n argument, allowing range input like 2-18.
    Ensures only even numbers are returned.
    """
    result: Set[int] = set()
    if "-" in n_input:
        try:
            start, end = map(int, n_input.split("-"))
            for n in range(start, end + 1):
                if n % 2 == 0:
                    result.add(n)
        except ValueError:
            print(f"[WARNING] Invalid range for -n: {n_input}")
    else:
        try:
            n = int(n_input)
            if n % 2 == 0:
                result.add(n)
            else:
                print(f"[WARNING] Skipping odd number: {n}")
        except ValueError:
            print(f"[WARNING] Invalid value for -n: {n_input}")
    return sorted(list(result))

def handle_gurobi_license():
    """Handles the Gurobi license file for the MIP solver."""
    src_path = '/src/MIP/gurobi.lic'
    dest_path = '/opt/gurobi/gurobi.lic'
    if os.path.exists(src_path):
        os.makedirs('/opt/gurobi', exist_ok=True)
        os.rename(src_path, dest_path)
        print("Gurobi license moved to /opt/gurobi/")

def build_command(model_path: str, n_teams: int | str, extra_args: str, specific_args: str, default_range: str) -> str:
    """Builds the full command string for a given model."""
    n_arg = f"-n {n_teams}" if n_teams != 'all' else f"-n {default_range}"
    return f"python3 {model_path} {specific_args} {n_arg} {extra_args}".strip()

def run_cp(n_teams: int | str, extra_args_str: str, config: dict):
    os.system(f"echo '--- running CP models ---'")
    os.chdir(config['path'])
    
    # Check for --help first
    if '--help' in extra_args_str:
        command = f"python3 {config['main_file']} --help"
        subprocess.run(command, shell=True)
        return

    extra_args_list = extra_args_str.split()
    run_all = '--all' in extra_args_list
    run_decisional = '--run_decisional' in extra_args_list
    run_optimal = '--run_optimization' in extra_args_list
    run_both = not run_decisional and not run_optimal
    
    solver_args_filtered = [arg for arg in extra_args_list if arg not in ['--run_decisional', '--run_optimization', '--all']]
    solver_args_str_filtered = " ".join(solver_args_filtered)
    
    if run_all:
        if run_decisional or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_decisional", config['default_range'])
            os.system(command)
        if run_optimal or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_optimization", config['default_range'])
            os.system(command)
    else:
        if run_decisional or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--run_decisional", config['default_range'])
            os.system(command)
        
        if run_optimal or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--run_optimization", config['default_range'])
            os.system(command)
    return

def run_sat(n_teams: int | str, extra_args_str: str, config: dict):
    os.system(f"echo '--- running SAT models ---'")
    os.chdir(config['path'])
    
    if '--help' in extra_args_str:
        command = f"python3 {config['main_file']} --help"
        subprocess.run(command, shell=True)
        return

    extra_args_list = extra_args_str.split()
    run_all = '--all' in extra_args_list
    run_decisional = '--run_decisional' in extra_args_list
    run_optimal = '--run_optimization' in extra_args_list
    run_both = not run_decisional and not run_optimal
    
    solver_args_filtered = [arg for arg in extra_args_list if arg not in ['--run_decisional', '--run_optimization', '--all']]
    solver_args_str_filtered = " ".join(solver_args_filtered)

    if run_all:
        if run_decisional or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_decisional", config['default_range'])
            os.system(command)
        if run_optimal or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_optimization", config['default_range'])
            os.system(command)
    else:
        if run_decisional or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--run_decisional", config['default_range'])
            os.system(command)
        
        if run_optimal or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--run_optimization", config['default_range'])
            os.system(command)
    return

def run_mip(n_teams: int | str, extra_args_str: str, config: dict):
    os.system(f"echo '--- running MIP models ---'")
    os.chdir(config['path'])
    
    if '--help' in extra_args_str:
        command = f"python3 {config['main_file']} --help"
        subprocess.run(command, shell=True)
        return

    extra_args_list = extra_args_str.split()
    run_all = '--all' in extra_args_list
    run_decisional = '--run_decisional' in extra_args_list
    run_optimal = '--run_optimization' in extra_args_list
    run_both = not run_decisional and not run_optimal
    
    solver_args_filtered = [arg for arg in extra_args_list if arg not in ['--run_decisional', '--run_optimization', '--all']]
    solver_args_str_filtered = " ".join(solver_args_filtered)
    
    if run_all:
        if run_decisional or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_decisional", config['default_range'])
            os.system(command)
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_decisional --ic false", config['default_range'])
            os.system(command)
        if run_optimal or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_optimization", config['default_range'])
            os.system(command)
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--all --run_optimization --ic true", config['default_range'])
            os.system(command)
    else:
        if run_decisional or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--run_decisional", config['default_range'])
            os.system(command)
        
        if run_optimal or run_both:
            command = build_command(config['main_file'], n_teams, solver_args_str_filtered, "--run_optimization", config['default_range'])
            os.system(command)
    
    return

def run_smt(n_teams: int | str, extra_args_str: str, config: dict):
    os.system(f"echo '--- running SMT models ---'")
    os.chdir(config['path'])

    if '--help' in extra_args_str:
        command = f"python3 {config['main_file']} --help"
        subprocess.run(command, shell=True)
        return

    extra_args_list = extra_args_str.split()
    run_all = '--all' in extra_args_list
    run_decisional = '--run_decisional' in extra_args_list
    run_optimal = '--run_optimization' in extra_args_list
    run_both = not run_decisional and not run_optimal
    
    n_teams = n_teams if n_teams != 'all' else parse_n_teams(config['default_range'])
    
    solver_args_filtered = [arg for arg in extra_args_list if arg not in ['--run_decisional', '--run_optimization', '--all']]
    solver_args_str_filtered = " ".join(solver_args_filtered)
    
    if run_all:
        for n in n_teams:
            if run_decisional or run_both:
                command = build_command(config['main_file_dec'], n, solver_args_str_filtered, "--approach_base z3_decisional", config['default_range'])
                os.system(command)
            if run_optimal or run_both:
                command = build_command(config['main_file_opt'], n, solver_args_str_filtered, "--approach_base z3_optimal", config['default_range'])
                os.system(command)
    else:
        for n in n_teams:
            if run_decisional or run_both:
                command = build_command(config['main_file_dec'], n, solver_args_str_filtered, "--approach_base z3_decisional", config['default_range'])
                os.system(command)
            if run_optimal or run_both:
                command = build_command(config['main_file_opt'], n, solver_args_str_filtered, "--approach_base z3_optimal", config['default_range'])
                os.system(command)
    return
    
   

def main():
    parser = argparse.ArgumentParser(description="Sport Tournament Scheduling.")
    
    parser.add_argument("-f", choices=['mip', 'cp', 'sat', 'smt'], help='Formulation to run')
    parser.add_argument("--run_all_formulations", action="store_true", help="Run all formulations with their default settings")
    
    parser.add_argument("-n", type=str, help="Problem size(s) to run")
    parser.add_argument("--run_all_sizes", action="store_true", help="Run all problem sizes for the specified formulation")
    
    args, extra_args = parser.parse_known_args()
    extra_args_str = " ".join(extra_args)

    handle_gurobi_license()

    models = {
        'cp': {'path': '/src/CP', 'main_file': '/src/CP/main.py', 'default_range': '2-18', 'run_func': run_cp},
        'sat': {'path': '/src/SAT', 'main_file': '/src/SAT/main.py', 'default_range': '2-20', 'run_func': run_sat},
        'smt': {'path': '/src/SMT', 'main_file_dec': '/src/SMT/decisional.py', 'main_file_opt': '/src/SMT/optimal.py', 'default_range': '6-20', 'run_func': run_smt},
        'mip': {'path': '/src/MIP', 'main_file': '/src/MIP/main.py', 'default_range': '6-18', 'run_func': run_mip},
    }
    
    n_to_run = args.n
    if args.run_all_sizes:
        n_to_run = 'all'

    if args.run_all_formulations:
        if args.f or args.n or args.run_all_sizes or (len(extra_args) > 0 and '--help' not in extra_args_str):
            print("[ERROR] Arguments are not allowed with --run_all_formulations.")
            sys.exit(1)
        for model_name, config in models.items():
            config['run_func'](config['default_range'], "--all", config)
    else:
        if not args.f and not '--help' in extra_args_str:
            print("[ERROR] You must specify a formulation with -f or use --run_all_formulations.")
            sys.exit(1)
        
        if not args.n and not args.run_all_sizes and '--help' not in extra_args_str and '--all' not in extra_args_str:
            print(f"[ERROR] Please specify -n, --run_all_sizes, or --all for formulation {args.f}.")
            sys.exit(1)
        
        config = models[args.f]
        config['run_func'](n_to_run, extra_args_str, config)
    return

if __name__ == '__main__':
    main()
