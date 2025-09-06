from pyomo.environ import ConcreteModel, RangeSet, Var, Binary, Constraint, Objective, \
    Integers, SolverFactory, minimize, ConstraintList, Param, Any, Set
import numpy as np
import time
import math
import os
from saveSolutions import saveSol


def circle_matchings(n):
    """Standard “pivot + circle” 1-factorization"""
    pivot, circle = n, list(range(1, n))
    weeks = n-1
    m = {}
    for w in range(1, weeks+1):
        ms = [(pivot-1, circle[w-1]-1)]
        for k in range(1, n//2):
            i = circle[(w-1 + k) % (n-1)]-1
            j = circle[(w-1 - k) % (n-1)]-1
            ms.append((i, j))
        m[w-1] = ms
    return m


def solveCircleMatching(n, optimization=True, ic=True, solver='cbc', timeout=300, verbose=False):
    start_cosntr = time.time()
    # utils
    l = [(i, j) for i in range(n) for j in range(n) if i < j]
    ij_to_match = {(i, j): idx for idx, (i, j) in enumerate(l)}

    model = ConcreteModel()
    model.W = RangeSet(0, (n-1)-1)
    model.P = RangeSet(0, (n//2)-1)
    model.I = RangeSet(0, n-1)
    model.M = RangeSet(0, (n*(n - 1)//2)-1)
    model.WP = Set(initialize=[(w, p) for w in model.W for p in model.P])
    model.match_teams = Param(model.M, initialize=lambda model, m: l[m], within=Any)
    # decision vars
    model.Y = Var(model.WP, model.M, domain=Binary)
    model.H = Var(model.M, domain=Binary)
    if optimization:
        # optimization vars
        model.Home = Var(model.I, domain=Integers, bounds=(0, n-1))
        model.Away = Var(model.I, domain=Integers, bounds=(0, n-1))
        model.Z = Var(domain=Integers, bounds=(0, n-1))

    # presolving
    presolved = np.zeros((n-1, n, n))
    pivot, circle = n, list(range(1, n))
    for w in range(1, n):
        presolved[w-1, circle[w-1]-1, pivot-1] = 1
        for k in range(1, n//2):
            i = circle[(w-1 + k) % (n-1)]-1
            j = circle[(w-1 - k) % (n-1)]-1
            if i < j:
                presolved[w-1, i, j] = 1
            else:
                presolved[w-1, j, i] = 1

    model.presolve_assignment = ConstraintList()
    for w in model.W:
        for p in model.P:
            for m in model.M:
                i, j = model.match_teams[m]
                model.presolve_assignment.add(
                    model.Y[(w, p), m] <= presolved[w, i, j])

    # necessary constraints
    def one_match_per_period_per_week_rule(model, w, p):
        return sum(model.Y[(w, p), m] for m in model.M) == 1
    model.one_match_per_period_per_week = Constraint(
        model.WP, rule=one_match_per_period_per_week_rule)

    def match_scheduled_once_rule(model, m):
        return sum(model.Y[wp, m] for wp in model.WP) == 1
    model.match_scheduled_once = Constraint(
        model.M, rule=match_scheduled_once_rule)

    model.max_team_match_period = ConstraintList()
    for p in model.P:
        for k in range(n):
            model.max_team_match_period.add(sum(model.Y[(w, p), ij_to_match[(k, j)]] for w in model.W for j in range(k+1, n)) +
                                            sum(model.Y[(w, p), ij_to_match[(i, k)]] for w in model.W for i in range(0, k)) <= 2)

    if ic:
        # additional constraints for efficiency
        model.Q = Var(model.I, model.P, domain=Binary)
        model.cover = ConstraintList()
        for i in model.I:
            for p in model.P:
                expr = sum(
                    model.Y[(w, p), ij_to_match[(i, j)]]
                    for w in model.W for j in range(i+1, n)
                ) + sum(
                    model.Y[(w, p), ij_to_match[(j, i)]]
                    for w in model.W for j in range(0, i)
                )
                model.cover.add(expr <= 2*model.Q[i, p])
        # Each team must appear in at least ceil((n-1)/2) distinct periods
        for i in model.I:
            model.cover.add(sum(model.Q[i, p]
                            for p in model.P) >= math.ceil((n-1)/2))

    if optimization:
        # objective constraints
        def home_games_rule(model, i):
            return model.Home[i] == sum(model.H[m] for m in model.M if i == model.match_teams[m][0]) + \
                sum(1 - model.H[m] for m in model.M if i == model.match_teams[m][1])
        model.home_games = Constraint(model.I, rule=home_games_rule)

        def away_games_rule(model, i):
            return model.Away[i] == sum(1 - model.H[m] for m in model.M if i == model.match_teams[m][0]) + \
                sum(model.H[m] for m in model.M if i == model.match_teams[m][1])
        model.away_games = Constraint(model.I, rule=away_games_rule)
        model.balance_max = Constraint(model.I, range(2), rule=lambda model, i, d:
                                       (model.Home[i] - model.Away[i] <= model.Z) if d == 0 else
                                       (model.Away[i] - model.Home[i] <= model.Z))
        model.obj = Objective(expr=model.Z, sense=minimize)
    else:
        model.obj = Objective(expr=1, sense=minimize)

    constr_time = time.time() - start_cosntr
    solver_factory = SolverFactory(solver)
    if solver == 'gurobi':
        solver_factory.options["TimeLimit"] = int(timeout-constr_time)
        solver_factory.options["threads"] = 1   # required
        solver_factory.options["MIPFocus"] = 3  # focus: 1-constr, 2-opt, 3-bound
    result = solver_factory.solve(
        model, tee=verbose, timelimit=int(timeout-constr_time))

    # solution extraction
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


def runCircleMatching(n, timeout=300, ic=True, optimization=True, verbose=False, save=True):
    solvers = ['cbc', 'glpk']
    if os.path.exists('/opt/gurobi/gurobi.lic') or os.path.exists('./gurobi.lic'):
        solvers.append('gurobi')

    outputs = []
    for solver in solvers:
        try:
            name = f"{'decision' if not optimization else 'optimization'}_{solver}_circleMatching_{'ic' if ic else 'no_ic'}"
            start = time.time()
            result, solution = solveCircleMatching(n, optimization, ic, solver, timeout, verbose)
            end = time.time()-start
            if solution.shape == (n-1, n//2, n, n):
                outputs.append((result, solution, end, name))

            print(f"CM, {n}, {'decision' if not optimization else 'optimization'}, {solver}, status: {result.Solver.status}, time: {end}")

        except Exception as e:
            if solver == 'gurobi':  # gurobi license error
                solvers.remove('gurobi')
            else:
                outputs.append(({}, [], 300, name))
    if save:
        saveSol(n, outputs, optimization, output_dir='/res/MIP',        
                filename=f'{n}.json', update=True)
    return
