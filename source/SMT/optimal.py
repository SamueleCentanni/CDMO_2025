import sys
import os
import json
import time
from z3 import *
from collections import defaultdict

def z3_label_periods_with_home_away(matches_per_week, periods, n, max_per_team=2, sb_enabled=True, timeout=290):
    """
    Build and solve the SMT optimization model with home/away balance.
    If sb_enabled is False, skip symmetry-breaking constraints.
    Returns: timetable, home_away, team_away_counts, imbalance_sum
    """
    weeks = sorted(matches_per_week.keys())
    # decision vars
    # 1) period assignment variables p[w,i,j] ∈ [1..periods]
    p = {(w,i,j): Int(f"p_{w}_{i}_{j}")
         for w in weeks
         for (i,j) in matches_per_week[w]}
    # 2) home/away indicator h[w,i,j] ∈ {0,1}: 1 if first team plays home, 0 otherwise
    h = {(w,i,j): Int(f"h_{w}_{i}_{j}")
         for w in weeks
         for (i,j) in matches_per_week[w]}

    opt = Optimize()
    opt.set(timeout=timeout * 1000)
    # domain
    for var in p.values():
        opt.add(var >= 1, var <= periods)
    for var in h.values():
        opt.add(var >= 0, var <= 1)

    # symmetry breaking: optional week1 period fixing
    if sb_enabled:
        w1 = weeks[0]
        for k, (i,j) in enumerate(sorted(matches_per_week[w1])):
            opt.add(p[w1,i,j] == k+1)

    # one match per slot per week
    for w in weeks:
        for k in range(1, periods+1):
            guards = [(p[w,i,j] == k, 1) for (i,j) in matches_per_week[w]]
            opt.add(PbEq(guards, 1))

    # at most max games per team per slot
    teams = {t for w in weeks for (i,j) in matches_per_week[w] for t in (i,j)}
    for t in teams:
        for k in range(1, periods+1):
            guards = [(p[w,i,j] == k, 1)
                      for w in weeks
                      for (i,j) in matches_per_week[w]
                      if t in (i,j)]
            opt.add(PbLe(guards, max_per_team))

    # away count and imbalance
    away_count = {}
    abs_diff = {}
    for t in teams:
        terms = []
        for w in weeks:
            for (i,j) in matches_per_week[w]:
                if i == t:
                    terms.append(1 - h[w,i,j])
                elif j == t:
                    terms.append(h[w,i,j])
        away_count[t] = Sum(terms)
        diff = (n - 1) - 2 * away_count[t]
        abs_diff[t] = If(diff >= 0, diff, -diff)

    # order abs_diff to minimize the maximal abs_diff later, and break abs_diff team symmetry
    for t1, t2 in zip(sorted(teams)[:-1], sorted(teams)[1:]):
        opt.add(abs_diff[t1] >= abs_diff[t2])

    sumDif = Int('sumDif')
    opt.add(sumDif == Sum([abs_diff[t] for t in sorted(teams)]))
    # optional lower bound
    opt.add(sumDif >= n)
    # objective: minimize maximum imbalance (abs_diff of first team)
    first_team = sorted(teams)[0]
    opt.minimize(abs_diff[first_team])

    # solve
    if opt.check() != sat:
        return None, None, None, None
    m = opt.model()

    # extract timetable
    timetable = {w: {} for w in weeks}
    for (w,i,j), var in p.items():
        slot = m[var].as_long()
        timetable[w][slot] = (i,j)

    # extract home/away
    home_away = {(w,i,j): m[h[w,i,j]].as_long()
                 for (w,i,j) in h}

    # compute team away counts and imbalance sum
    team_away_counts = {t: m.evaluate(abs_diff[t]).as_long() for t in teams}
    imbalance_sum = m.evaluate(sumDif).as_long()

    return timetable, home_away, team_away_counts, imbalance_sum

# presolve: matching and balancing

def circle_matchings(n):
    pivot, circle = n, list(range(1, n))
    weeks = n - 1
    m = {}
    for w in range(1, weeks+1):
        ms = [(pivot, circle[w-1])]
        for k in range(1, n//2):
            i = circle[(w-1 + k) % (n-1)]
            j = circle[(w-1 - k) % (n-1)]
            ms.append((i,j))
        m[w] = ms
    return m

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Optim. solver with home/away and optional SB.')
    parser.add_argument('n', type=int, help='Number of teams (even)')
    parser.add_argument('approach_base', help='Base name for the approach in JSON')
    parser.add_argument('--sb_disabled', action='store_true', help='Disable symmetry breaking')
    args = parser.parse_args()

    n = args.n
    sb_enabled = not args.sb_disabled
    suffix = '_sb_enabled' if sb_enabled else '_sb_disabled'
    approach = args.approach_base + suffix

    # benchmark start
    t0 = time.time()
    matches = circle_matchings(n)
    periods = n // 2
    timetable, home_away, counts, imbalance = z3_label_periods_with_home_away(
        matches, periods, n, sb_enabled=sb_enabled)
    t2 = time.time()

    total_time = min(int(t2 - t0), 300)
    optimal = timetable is not None
    obj = imbalance

    # Transpose timetable to periods x weeks, ordering teams by home_away indicator
    sol_periods = []
    for p_idx in range(periods):
        period = p_idx + 1
        row = []
        for w in sorted(timetable):
            i, j = timetable[w][period]
            # if h=1 first team is home, else swap
            if home_away.get((w, i, j), 1) == 1:
                row.append([i, j])
            else:
                row.append([j, i])
        sol_periods.append(row)

    # write JSON
    folder = '/res/SMT'
    os.makedirs(folder, exist_ok=True)
    json_path = os.path.join(folder, f'{n}.json')
    if os.path.exists(json_path):
        with open(json_path) as f:
            data = json.load(f)
    else:
        data = {}

    data[approach] = {
        'time': total_time,
        'optimal': optimal,
        'obj': obj,
        'sol': sol_periods
    }
    with open(json_path, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Solved {approach} for {n} teams in {total_time} seconds")