import sys
import os
import json
import time
from z3 import *
from collections import defaultdict

def z3_label_periods(matches_per_week, periods, max_per_team=2, sb_enabled=True, timeout=290):
    """
    Build and solve the SMT model. If sb_enabled is False, skip symmetry-breaking constraints.
    """
    weeks = sorted(matches_per_week.keys())
    # decision vars
    # 1) period assignment variables p[w,i,j] ∈ [1..periods]
    p = { (w,i,j): Int(f"p_{w}_{i}_{j}")
          for w in weeks
          for (i,j) in matches_per_week[w] }

    # directive for solver to convert cardinality constraints to bit-vectors
    solver = Then('card2bv','smt').solver()
    solver.set(timeout=timeout * 1000)

    # domain constraints
    for var in p.values():
        solver.add(var >= 1, var <= periods)

    # symmetry breaking: optional week1 period fixing
    if sb_enabled:
        w1 = weeks[0]
        for k, (i,j) in enumerate(sorted(matches_per_week[w1])):
            solver.add(p[w1,i,j] == k+1)

    # one match per slot per week
    for w in weeks:
        for k in range(1, periods+1):
            guards = [(p[w,i,j] == k, 1) for (i,j) in matches_per_week[w]]
            solver.add(PbEq(guards, 1))

    # at most max games per team per slot
    teams = {t for w in weeks for (i,j) in matches_per_week[w] for t in (i,j)}
    for t in teams:
        for k in range(1, periods+1):
            guards = [(p[w,i,j] == k, 1)
                      for w in weeks
                      for (i,j) in matches_per_week[w]
                      if t in (i,j)]
            solver.add(PbLe(guards, max_per_team))

    # solve
    solver.check()
    m = solver.model()

    # build as weeks x periods
    sol = []
    for w in weeks:
        row = []
        for k in range(1, periods+1):
            for (a,b) in matches_per_week[w]:
                if m[p[w,a,b]].as_long() == k:
                    row.append([a, b])
                    break
        sol.append(row)
    return sol

# presolve: matching and balancing

def circle_matchings(n):
    pivot, circle = n, list(range(1,n))
    weeks = n-1
    m = {}
    for w in range(1, weeks+1):
        ms = [(pivot, circle[w-1])]
        for k in range(1, n//2):
            i = circle[(w-1 + k) % (n-1)]
            j = circle[(w-1 - k) % (n-1)]
            ms.append((i,j))
        m[w] = ms
    return m


def home_away_balance(matches_per_week, n):
    balanced = {}
    for w, matches in matches_per_week.items():
        row = []
        for (i,j) in matches:
            d = (j - i) % n
            row.append((i,j) if d < n//2 else (j,i))
        balanced[w] = row
    return balanced

if __name__ == '__main__':
    # usage: python decisional.py <n> <approach_base> [--sb_disabled]
    import argparse
    parser = argparse.ArgumentParser(description='Decisional solver with optional SB.')
    parser.add_argument('n', type=int, help='Number of teams (even)')
    parser.add_argument('approach_base', help='Base name for the approach in JSON')
    parser.add_argument('--sb_disabled', action='store_true', help='Disable symmetry breaking')
    args = parser.parse_args()

    n = args.n
    sb_enabled = not args.sb_disabled
    suffix = '_sb_enabled' if sb_enabled else '_sb_disabled'
    approach = args.approach_base + suffix

    # presolve + solve benchmark
    t0 = time.time()
    raw = circle_matchings(n)
    matches = home_away_balance(raw, n)
    periods = n // 2
    sol_weeks = z3_label_periods(matches, periods, sb_enabled=sb_enabled)
    t2 = time.time()

    # transpose to periods x weeks
    sol_periods = []
    num_weeks = len(sol_weeks)
    for p in range(periods):
        row = []
        for w in range(num_weeks):
            row.append(sol_weeks[w][p])
        sol_periods.append(row)

    total_time = min(int(t2 - t0), 300)
    optimal = sol_periods is not None
    obj = None

    # get the directory where the current script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # write json
    folder = os.path.join(script_dir, 'res', 'SMT')
    os.makedirs(folder, exist_ok=True)
    json_path = os.path.join(folder, f'{n}.json')

    # load existing data
    if os.path.exists(json_path):
        with open(json_path) as f:
            data = json.load(f)
    else:
        data = {}

    # append/update
    data[approach] = {
        'time': total_time,
        'optimal': optimal,
        'obj': obj,
        'sol': sol_periods
    }

    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    #print(f"Results for '{approach}' appended to {json_path}")
