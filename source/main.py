#!/usr/bin/env python
import os
import argparse
from SAT.main import runAllSAT
from MIP.circleMatching import runAllCircleMatching, runCircleMatching
from MIP._4dArray import runAll4dArray

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run circle matching and 4d array solvers.")
    parser.add_argument('-f', choices=['all', 'mip', 'cp', 'sat', 'smt'], default='all', help='Solver type to run')
    parser.add_argument('-n', choices=['all', '6', '8', '10', '12'], default='all', help='Problem size to run')
    args = parser.parse_args()

    # handle commercial solver license
    if os.path.exists('/src/MIP/gurobi.lic'):
        os.makedirs('/opt/gurobi', exist_ok=True)
        os.rename('/src/MIP/gurobi.lic', '/opt/gurobi/gurobi.lic')

    if args.f == 'all' and args.n == 'all':
        # CP
        # print("--- running all CP models ---")
        # SAT
        # runAllSAT()
        print("--- running all SAT models ---")
        os.system("python /src/SAT/main.py --run_decisional --run_optimization --all")
        # SMT
        # print("--- running all SMT models ---")

        # MIP models
        print("--- running all MIP models ---")
        # runAllCircleMatching()
        # runAll4dArray()
    else:
        if args.f == 'cp':
            pass
        elif args.f == 'sat':
            pass
        elif args.f == 'smt':
            pass
        elif args.f == 'mip':
            if args.n == 'all':
                runAllCircleMatching()
            else:
                runCircleMatching(int(args.n))