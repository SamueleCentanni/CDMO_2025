import os
import argparse
import re


def parse_n_teams(n_input):
    """
    Parses the input for -n argument, allowing range input like 2-18.
    Ensures only even numbers are returned.
    """
    result = set()
    if "-" in n_input:
        start, end = map(int, n_input.split("-"))
        for n in range(start, end + 1):
            if n % 2 == 0:
                result.add(n)
    else:
        try:
            n = int(n_input)
            if n % 2 == 0:
                result.add(n)
            else:
                print(f"[WARNING] Skipping odd number: {n}")
        except ValueError:
            print(f"[WARNING] Invalid value for -n: {n_input}")
    return sorted(result)

def main():
    parser = argparse.ArgumentParser(description="Run circle matching and 4d array solvers.")
    parser.add_argument('-f', required=True, choices=['all', 'mip', 'cp', 'sat', 'smt'], default='all', help='Formulation to run')
    parser.add_argument("-n", required=True, type=str, default=["6-20"], help="Problem size(s) to run")
    args = parser.parse_args()

    # handle commercial solver license
    if os.path.exists('/src/MIP/gurobi.lic'):
        os.makedirs('/opt/gurobi', exist_ok=True)
        os.rename('/src/MIP/gurobi.lic', '/opt/gurobi/gurobi.lic')

    # run everything
    if args.f == 'all' and args.n == 'all':
        # CP
        os.system("echo '--- running all CP models ---'")
        os.chdir("/src/CP")
        os.system("python3 /src/CP/main.py --run_decisional --run_optimization --all -n 6-18 --save_json")
        # SAT
        os.system("echo '--- running all SAT models ---'")
        os.chdir("/src/SAT")
        os.system("python3 /src/SAT/main.py --run_decisional --run_optimization --all --save_json")
        # SMT
        os.system("echo '--- running all SMT models ---'")
        os.chdir("/src/SMT")
        for n in range(6,20,2):
            os.system(f"python3 /src/SMT/decisional.py {n} z3_decisional --sb_disabled")
            os.system(f"python3 /src/SMT/optimal.py {n} z3_optimal --sb_disabled")
        # MIP models
        os.system("echo '--- running all MIP models ---'")
        os.chdir("/src/MIP")
        os.system("python3 /src/MIP/main.py --run_decisional --run_optimization --all")
    elif args.f == 'all' :
        os.system("echo '--- running CP models ---'")
        os.chdir("/src/CP")
        os.system(f"python3 /src/CP/main.py --run_decisional --run_optimization --all -n {args.n} --save_json")
        os.system("echo '--- running all SAT models ---'")
        os.chdir("/src/SAT")
        os.system(f"python3 /src/SAT/main.py --run_decisional --run_optimization --all -n {args.n} --save_json")
        os.system("echo '--- running all SAT models ---'")
        os.chdir("/src/SAT")
        for n in parse_n_teams(args.n):
            os.system(f"python3 /src/SMT/decisional.py {n} z3_decisional --sb_disabled")
            os.system(f"python3 /src/SMT/optimal.py {n} z3_optimal --sb_disabled")
        os.system("echo '--- running all MIP models ---'")
        os.chdir("/src/MIP")
        os.system(f"python3 /src/MIP/main.py --all -n {args.n}")
    else:
        assert args.f == 'cp' or args.f == 'sat' or args.f == 'smt' or args.f == 'mip', "Specify one formulation"
        if args.f == 'cp':
            os.chdir("/src/CP")
            if args.n == 'all':
                os.system(f"python3 /src/CP/main.py --run_decisional --run_optimization --all -n 6-18 --save_json")
            else:
                os.system(f"python3 /src/CP/main.py --run_decisional --run_optimization --all -n {args.n} --save_json")
        elif args.f == 'sat':
            os.chdir("/src/SAT")
            if args.n == 'all':
                os.system("python3 /src/SAT/main.py --run_decisional --run_optimization --all --save_json")
            else:
                os.system(f"python3 /src/SAT/main.py --run_decisional --run_optimization --all -n {args.n} --save_json")
        elif args.f == 'smt':
            os.chdir("/src/SMT")
            if args.n == 'all':
                for n in range(6,20,2):
                    os.system(f"python3 /src/SMT/decisional.py {n} z3_decisional --sb_disabled")
                    os.system(f"python3 /src/SMT/optimal.py {n} z3_optimal --sb_disabled")
            else:
                for n in parse_n_teams(args.n):
                    os.system(f"python3 /src/SMT/decisional.py {n} z3_decisional --sb_disabled")
                    os.system(f"python3 /src/SMT/optimal.py {n} z3_optimal --sb_disabled")
        elif args.f == 'mip':
            os.chdir("/src/MIP")
            if args.n == 'all':
                os.system(f"python3 /src/MIP/main.py --all -n 6-18")
            else:
                os.system(f"python3 /src/MIP/main.py --all -n {args.n}")

    return

if __name__ == '__main__':
    main()