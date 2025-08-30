import os
import argparse
# from MIP.circleMatching import runAllCircleMatching, runCircleMatching
# from MIP._4dArray import runAll4dArray


def main():
    parser = argparse.ArgumentParser(description="Run circle matching and 4d array solvers.")
    parser.add_argument('-f', choices=['all', 'mip', 'cp', 'sat', 'smt'], default='all', help='Formulation to run')
    parser.add_argument('-n', choices=['all', '6', '8', '10', '12', '14', '16', '18', '20'], default='all', help='Problem size to run')
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
        # runAllCircleMatching()
        # runAll4dArray()
    # else:
    #     if args.f == 'cp':
    #         pass
    #     elif args.f == 'sat':
    #         pass
    #     elif args.f == 'smt':
    #         pass
    #     elif args.f == 'mip':
    #         if args.n == 'all':
                # runAllCircleMatching()
            # else:
                # runCircleMatching(int(args.n))
    return

if __name__ == '__main__':
    main()