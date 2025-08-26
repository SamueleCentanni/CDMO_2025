from pyomo.environ import ConcreteModel, RangeSet, Var, Binary, Constraint, Objective, \
  NonNegativeIntegers, Integers, SolverFactory, minimize, ConstraintList, Param, Any, Set, \
  NonNegativeReals, quicksum
import numpy as np
import time, math, json, os


def solveWarmStart(n, opt=True, solver='cbc', verbose=False):
    start_cosntr = time.time()
    l = [(i, j) for i in range(n) for j in range(n) if i < j]
    ij_to_match = {(i, j): idx for idx, (i, j) in enumerate(l)}

    model = ConcreteModel()
    model.W = RangeSet(0, (n-1)-1)
    model.P = RangeSet(0, (n//2)-1)
    model.I = RangeSet(0, n-1)
    model.J = RangeSet(0, n-1)
    model.M = RangeSet(0, (n*(n - 1)//2)-1)
    model.WP = Set(initialize=[(w, p) for w in model.W for p in model.P])
    model.match_teams = Param(model.M, initialize=lambda model, m: l[m], within=Any)

    # decision vars
    model.Y = Var(model.WP, model.M, domain=Binary)
    model.H = Var(model.M, domain=Binary)
    if opt:
        # optimization vars
        model.Home = Var(model.I, domain=Integers, bounds=(0, n-1))
        model.Away = Var(model.I, domain=Integers, bounds=(0, n-1))
        model.Z = Var(domain=Integers, bounds=(0, n-1))

    # constraints
    model.max_one_match_per_week = ConstraintList()
    for w in model.W:
        for k in model.I:
            model.max_one_match_per_week.add(
                sum(model.Y[(w, p), ij_to_match[(k, j)]] for p in model.P for j in range(k + 1, n))
                + sum(model.Y[(w, p), ij_to_match[(i, k)]] for p in model.P for i in range(0, k))
                <= 1
            )

    def one_match_per_period_per_week_rule(model, w, p):
        return sum(model.Y[(w, p), m] for m in model.M) == 1
    model.one_match_per_period_per_week = Constraint(model.WP, rule=one_match_per_period_per_week_rule)

    def match_scheduled_once_rule(model, m):
        return sum(model.Y[wp, m] for wp in model.WP) == 1
    model.match_scheduled_once = Constraint(model.M, rule=match_scheduled_once_rule)

    model.max_team_match_period = ConstraintList()
    for p in model.P:
        for k in range(n):
            model.max_team_match_period.add(
                sum(model.Y[(w, p), ij_to_match[(k, j)]] for w in model.W for j in range(k+1, n))
                + sum(model.Y[(w, p), ij_to_match[(i, k)]] for w in model.W for i in range(0, k)) <= 2
            )

    def tot_matches_rule(model):
        return sum(model.Y[wp, m] for wp in model.WP for m in model.M) == n*(n - 1)//2
    model.tot_matches = Constraint(rule=tot_matches_rule)

    if opt:
        # objective constraints
        def home_games_rule(model, i):
            return model.Home[i] == sum(model.H[m] for m in model.M if i == model.match_teams[m][0]) \
                                 + sum(1 - model.H[m] for m in model.M if i == model.match_teams[m][1])
        model.home_games = Constraint(model.I, rule=home_games_rule)

        def away_games_rule(model, i):
            return model.Away[i] == sum(1 - model.H[m] for m in model.M if i == model.match_teams[m][0]) \
                                 + sum(model.H[m] for m in model.M if i == model.match_teams[m][1])
        model.away_games = Constraint(model.I, rule=away_games_rule)

        model.balance_max = Constraint(model.I, range(2), rule=lambda model, i, d:
            (model.Home[i] - model.Away[i] <= model.Z) if d == 0 else
            (model.Away[i] - model.Home[i] <= model.Z)
        )

        model.obj = Objective(expr=model.Z, sense=minimize)
    else:
        model.obj = Objective(expr=1, sense=minimize)

    # greedy warm start: assign matches sequentially
    wp_list = list(model.WP)
    for m in model.M:
        (i, j) = model.match_teams[m]
        wp = wp_list[m % len(wp_list)]
        model.Y[wp, m].value = 1  # schedule match m at this (w, p)
        model.H[m].value = 1 if i < j else 0  # arbitrary home choice

    # approximate home/away counts
    for i in model.I:
        model.Home[i].value = n // 2
        model.Away[i].value = n // 2
    model.Z.value = 1

    constr_time = time.time() - start_cosntr

    solver = SolverFactory(solver)
    solver.options['Threads'] = 1

    # Some solvers support warmstart explicitly
    # try:
    result = solver.solve(model, tee=False, warmstart=True, timelimit=int(300-constr_time-1))
    # except:
    #     result = solver.solve(model, tee=False, timelimit=int(300-constr_time-1))

    solution = np.zeros((n-1, n//2, n, n))
    for w in model.W:
        for p in model.P:
            for m in model.M:
                if model.Y[(w, p), m].value is not None and abs(model.Y[(w, p), m].value) > 1e-6:
                    i, j = model.match_teams[m]
                    if model.H[m].value == 1:
                        solution[w, p, i, j] = 1
                    else:
                        solution[w, p, j, i] = 1

    return result, solution

def saveSol(n, result, solution, time, opt=True, solver='cbc', filename='data.json'):
    formatted_sol = []
    for p in range(n//2):
        row = []
        for w in range(n-1):
            for i in range(n):
                for j in range(n):
                    if solution[w,p,i,j] == 1:
                        row.append([i+1, j+1])
        formatted_sol.append(row)

    obj = result.Problem.Upper_bound
    output = {
        "sol": formatted_sol,
        "time": math.floor(time),
        "optimal": True and obj == 1,
        "obj": result.Problem.Upper_bound if opt else None,
    }

    # for docker
    # output_dir = '/MIP/res'
    output_dir = '../../res/MIP'
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        json.dump({solver:output}, f, ensure_ascii=False, indent=4)

def runAllWarmStart():
    solver='cbc'
    for n in range(6,14,2):
        start = time.time()
        result, solution = solveWarmStart(n, opt=True, solver=solver, verbose=False)
        end = time.time()-start
        saveSol(n, result, solution, end, opt=True, solver=solver, filename=f'circleMatching_{n}.json')
        
        print(result)
        print(end)


if __name__ == "__main__":
    solver='cbc'
    for n in range(6,18,2):
        start = time.time()
        result, solution = solveWarmStart(n, opt=True, solver=solver, verbose=False)
        end = time.time()-start
        # saveSol(n, result, solution, end, opt=True, solver=solver, filename=f'circleMatching_{n}.json')

        print(result)
        print(end)