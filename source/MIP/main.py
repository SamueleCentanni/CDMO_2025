import os
import argparse
import re
from itertools import product
from circleMatching import runAllCircleMatching, runCircleMatching
from _4dArray import runAll4dArray, run4dArray


def parse_n_teams(n_input):
    """
    Parses the input for -n argument, allowing range input like 2-18.
    Ensures only even numbers are returned.
    """
    result = set()
    for item in n_input:
        if re.match(r"^\d+-\d+$", item):  # range type: 2-18
            start, end = map(int, item.split("-"))
            for n in range(start, end + 1):
                if n % 2 == 0:
                    result.add(n)
        else:  # single value
            try:
                n = int(item)
                if n % 2 == 0:
                    result.add(n)
                else:
                    print(f"[WARNING] Skipping odd number: {n}")
            except ValueError:
                print(f"[WARNING] Invalid value for -n: {item}")
    return sorted(result)

def main():
    parser = argparse.ArgumentParser(description="Sport Tournament Scheduler with MIP formulation.")
    parser.add_argument(
        "-n", "--n_teams",
        type=str,
        nargs='+',
        default=["2-20"],
        help="List of even numbers or ranges like 2-18 for number of teams to test."
    )
    parser.add_argument(
        "-t", "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each solver instance."
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all methods."
    )
    parser.add_argument(
        "--_4D",
        action="store_true",
        help="Run the 4D array model."
    )
    parser.add_argument(
        "--CM",
        action="store_true",
        help="Run the circle matching model."
    )
    parser.add_argument(
        "--run_decisional",
        action="store_true",
        help="Run the decisional solver."
    )
    parser.add_argument(
        "--run_optimization",
        action="store_true",
        help="Run the optimization solver."
    )
    parser.add_argument(
        "--ic",
        dest="ic",
        type=bool,
        default=True,
        help="Enable implied constraints."
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output."
    )
    parser.add_argument(
        "--save_json",
        action='store_true',
        default=True,
        help="Save solver results to JSON files."
    )

    args = parser.parse_args()

    # Parse and validate number of teams
    args.n_teams = parse_n_teams(args.n_teams)
    for n in args.n_teams:
        assert args.all or args.CM or args._4D, "Specify at least one model to run: --CM or --_4D"
        assert args.all or args.run_decisional or args.run_optimization, "Specify at least one solver type to run: --run_decisional or --run_optimization"
        if args.all:
            runCircleMatching(n, args.timeout, ic=False, optimization=False, verbose=args.verbose, save=args.save_json)
            runCircleMatching(n, args.timeout, ic=True, optimization=False, verbose=args.verbose, save=args.save_json)
            run4dArray(n, args.timeout, ic=False, optimization=False, verbose=args.verbose, save=args.save_json)
            run4dArray(n, args.timeout, ic=True, optimization=False, verbose=args.verbose, save=args.save_json)
            runCircleMatching(n, args.timeout, ic=False, optimization=True, verbose=args.verbose, save=args.save_json)
            runCircleMatching(n, args.timeout, ic=True, optimization=True, verbose=args.verbose, save=args.save_json)
            run4dArray(n, args.timeout, ic=False, optimization=True, verbose=args.verbose, save=args.save_json)
            run4dArray(n, args.timeout, ic=True, optimization=True, verbose=args.verbose, save=args.save_json)
        else:
            if args.CM:
                if args.run_decisional:
                    runCircleMatching(n, args.timeout, args.ic, optimization=False, verbose=args.verbose, save=args.save_json)
                if args.run_optimization:
                    runCircleMatching(n, args.timeout, args.ic, optimization=True, verbose=args.verbose, save=args.save_json)
            if args._4D:
                if args.run_decisional:
                    run4dArray(n, args.timeout, args.ic, optimization=False, verbose=args.verbose, save=args.save_json)
                if args.run_optimization:
                    run4dArray(n, args.timeout, args.ic, optimization=True, verbose=args.verbose, save=args.save_json)
    return

if __name__ == "__main__":
    main()