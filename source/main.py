import os
import argparse

def main():
    parser = argparse.ArgumentParser(description="Run circle matching and 4d array solvers.")
    parser.add_argument('-f', required=True, choices=['all', 'mip', 'cp', 'sat', 'smt'], default='all', help='Formulation to run')
    parser.add_argument("-n", required=True, type=str, default=["2-20"], help="Problem size(s) to run")
    args = parser.parse_args()

    # handle commercial solver license
    if os.path.exists('/src/MIP/gurobi.lic'):
        os.makedirs('/opt/gurobi', exist_ok=True)
        os.rename('/src/MIP/gurobi.lic', '/opt/gurobi/gurobi.lic')

    if args.f == 'all' and args.n == 'all':
        # CP
        os.system("echo '--- running all CP models ---'")
        os.chdir("/src/CP")
        os.system("python3 /src/CP/main.py --run_decisional --run_optimization --all -n 6-18 --save_json")
        # SAT
        os.system("echo '--- running all SAT models ---'")
        os.chdir("/src/SAT")
        os.system("python3 /src/SAT/main.py --run_decisional --run_optimization --all")
        # SMT
        os.system("echo '--- running all SMT models ---'")
        os.chdir("/src/SMT")
        for n in range(6,8,2):
            os.system(f"python3 /src/SMT/decisional.py {n} z3_decisional --sb_disabled")
            os.system(f"python3 /src/SMT/optimal.py {n} z3_optimal --sb_disabled")
        # MIP models
        os.system("echo '--- running all MIP models ---'")
        os.chdir("/src/MIP")
        os.system("python3 /src/MIP/main.py --run_decisional --run_optimization --all")

    else:
        assert args.f == 'cp' or args.f == 'sat' or args.f == 'smt' or args.f == 'mip', "Specify one formulation"
        if args.f == 'cp':
            pass
        elif args.f == 'sat':
            pass
        elif args.f == 'smt':
            pass
        elif args.f == 'mip':
            os.chdir("/src/MIP")
            os.system(f"python3 /src/MIP/main.py --all -n {args.n}")

    return

if __name__ == '__main__':
    main()