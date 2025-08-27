from pyomo.environ import ConcreteModel, RangeSet, Var, Binary, Constraint, Objective, \
    NonNegativeIntegers, SolverFactory, minimize, ConstraintList, NonNegativeReals
import numpy as np
import time
import math
import json
import os


def solve4dArray(n, opt=True, solver='cbc', verbose=False):
    start_cosntr = time.time()
    model = ConcreteModel()
    model.W = RangeSet(0, (n-1)-1)
    model.P = RangeSet(0, (n//2)-1)
    model.I = RangeSet(0, n-1)
    model.J = RangeSet(0, n-1)
    # decision var
    model.X = Var(model.W, model.P, model.I, model.J, domain=Binary)
    if opt:
        # optimization vars
        model.home = Var(model.I, domain=NonNegativeIntegers)
        model.away = Var(model.I, domain=NonNegativeIntegers)

    # constraints
    def one_match_rule(model, i):
        return (
            sum(model.X[w, p, i, j] for w in model.W for p in model.P for j in model.J) +
            sum(model.X[w, p, j, i] for w in model.W for p in model.P for j in model.J)
            == n - 1
        )
    def symmetry_rule(model, i, j):
        if i < j:
            return (
                sum(model.X[w, p, i, j] for w in model.W for p in model.P) +
                sum(model.X[w, p, j, i] for w in model.W for p in model.P)
                == 1
            )
        else:
            return Constraint.Skip
    def one_match_per_week_rule(model, w, i):
        return sum(model.X[w, p, i, j] + model.X[w, p, j, i] for p in model.P for j in model.J if j != i) <= 1
    def max_one_per_period_per_week_rule(model, w, i, j):
        return sum(model.X[w, p, i, j] for p in model.P) <= 1
    def max_one_game_per_match_rule(model, i, j):
        return sum(model.X[w, p, i, j] for w in model.W for p in model.P) <= 1
    def max_two_matches_per_period_rule(model, i, p):
        return (
            sum(model.X[w, p, i, j] for w in model.W for j in model.J) +
            sum(model.X[w, p, j, i] for w in model.W for j in model.J)
            <= 2
        )
    def one_game_per_team_per_week_rule(model, w, i):
        return sum(model.X[w, p, i, j] for p in model.P for j in model.J) + sum(model.X[w, p, j, i] for p in model.P for j in model.J) == 1
    def one_match_per_period_per_week_rule(model, w, p):
        return sum(model.X[w,p,i,j] for i in model.I for j in model.J) == 1
    model.one_match_per_team = Constraint(model.I, rule=one_match_rule)
    model.symmetry = Constraint(model.I, model.J, rule=symmetry_rule)
    model.one_match_per_week = Constraint(model.W, model.I, rule=one_match_per_week_rule)
    model.max_one_per_period_per_week = Constraint(model.W, model.I, model.J, rule=max_one_per_period_per_week_rule)
    model.max_one_game_per_match = Constraint(model.I, model.J, rule=max_one_game_per_match_rule)
    model.max_two_matches_per_period = Constraint(model.I, model.P, rule=max_two_matches_per_period_rule)
    model.one_game_per_team_per_week = Constraint(model.W, model.I, rule=one_game_per_team_per_week_rule)
    model.one_match_per_period_per_week = Constraint(model.W, model.P, rule=one_match_per_period_per_week_rule)

    # additional constraints for efficiency
    def tot_matches_rule(model):
        return sum(model.X[w,p,i,j] for w in model.W for p in model.P for i in model.I for j in model.J) == n*(n - 1)//2
    def no_self_match_rule(model, i):
        return sum(model.X[w, p, i, i] for w in model.W for p in model.P) == 0
    model.tot_matches = Constraint(rule=tot_matches_rule)
    model.no_self_match = Constraint(model.I, rule=no_self_match_rule)

    # symmetry breaking
    def fix_first_week_rule(model, p):
        i = 2 * p
        j = 2 * p + 1
        return model.X[0, p, i, j] == 1  # Fix home/away arbitrarily
    def fix_team0_schedule_rule(model, w):
        j = w + 1
        return sum(model.X[w, p, 0, j] + model.X[w, p, j, 0] for p in model.P) == 1
    model.fix_first_week = Constraint(model.P, rule=fix_first_week_rule)
    model.team0_schedule = Constraint(model.W, rule=fix_team0_schedule_rule)

    # objective function
    if opt:        
        # auxiliary constraints for obj function
        def home_games_rule(model, i):
            return model.home[i] == sum(model.X[w, p, i, j] for w in model.W for p in model.P for j in model.J if i != j)
        def away_games_rule(model, i):
            return model.away[i] == sum(model.X[w, p, j, i] for w in model.W for p in model.P for j in model.J if i != j)
        model.home_games = Constraint(model.I, rule=home_games_rule)
        model.away_games = Constraint(model.I, rule=away_games_rule)
        model.z = Var(domain=NonNegativeReals)
        model.balance_max = ConstraintList()
        for i in model.I:
            model.balance_max.add(model.home[i] - model.away[i] <= model.z)
            model.balance_max.add(model.away[i] - model.home[i] <= model.z)
        model.obj = Objective(expr=model.z, sense=minimize)
    else:
        model.obj = Objective(expr=1, sense=minimize)

    constr_time = time.time() - start_cosntr
    solver_factory = SolverFactory(solver)
    if solver == 'gurobi':
        solver_factory.options["threads"] = 1   # required
        solver_factory.options["MIPFocus"] = 3  # focus: 1-constr, 2-opt, 3-bound
    result = solver_factory.solve(model, tee=verbose, timelimit=int(300-constr_time))

    solution = np.zeros((n-1, n//2, n, n))
    for i in model.X.get_values().keys():
        if model.X[i].value is not None and abs(model.X[i].value) > 1e-6:
            solution[i[0], i[1], i[2], i[3]] = 1
    return result, solution

def saveSol(n, solvers, outputs, opt=True, output_dir='../../res/MIP', filename='data.json'):
    output = {}
    for h,o in enumerate(outputs):
        result, solution, time = o
        formatted_sol = []
        for p in range(n//2):
            row = []
            for w in range(n-1):
                for i in range(n):
                    for j in range(n):
                        if solution[w, p, i, j] == 1:
                            row.append([i+1, j+1])
            formatted_sol.append(row)
        time  = math.floor(time)
        obj = result.Problem.Upper_bound
        optimal = not opt or (obj == 1 and time < 299)
        output[solvers[h]] = {
            "sol": formatted_sol,
            "time": time if optimal else 300,
            "optimal": optimal,
            "obj": obj if opt else None,
        }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)

def updateSol(n, solvers, outputs, opt=True, output_dir='../../res/MIP', filename='data.json'):
    output = {}
    try:
        with open(os.path.join(output_dir, filename), 'r', encoding='utf-8') as f:
            output = json.load(f)
    except:
        pass
    for h,o in enumerate(outputs):
        result, solution, time = o
        formatted_sol = []
        for p in range(n//2):
            row = []
            for w in range(n-1):
                for i in range(n):
                    for j in range(n):
                        if solution[w, p, i, j] == 1:
                            row.append([i+1, j+1])
            formatted_sol.append(row)
        time  = math.floor(time)
        obj = result.Problem.Upper_bound
        optimal = not opt or (obj == 1 and time < 299)
        output[solvers[h]] = {
            "sol": formatted_sol,
            "time": time if optimal else 300,
            "optimal": optimal,
            "obj": obj if opt else None,
        }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)


def runAll4dArray():
    solvers = ['cbc', 'glpk']
    if os.path.exists('/opt/gurobi/gurobi.lic'):
        solvers.append('gurobi')
    if solvers == []:
        raise ValueError("No solver available")
    for n in range(6,18,2):
        print(f"--- n: {n} ---")
        outputs = []
        for solver in solvers:
            try:
                start = time.time()
                result, solution = solve4dArray(
                    n, opt=True, solver=solver, verbose=False)
                end = time.time()-start
                if solution.shape == (n-1, n//2, n, n):
                    outputs.append((result, solution, end))
                elif end >= 299:
                    solvers.remove(solver)

                print(f"solver: {solver}")
                print(f"status: {result.Solver.status}")
                print(f"time: {end}")
            except:
                if solver == 'gurobi':  # gurobi license error
                    solvers.remove('gurobi')

        saveSol(n, solvers, outputs, opt=True, output_dir='/res/MIP',
                filename=f'4dArray_{n}.json')


if __name__ == "__main__":
    solvers = []
    if os.path.exists('gurobi.lic'):
        solvers.append('gurobi')
    if solvers == []:
        raise ValueError("No solver available")
    # for n in [12]:
    for n in range(6,18,2):
        print(f"--- n: {n} ---")
        outputs = []
        for solver in solvers:
            print(f"solver: {solver}")
            start = time.time()
            result, solution = solve4dArray(
                n, opt=True, solver=solver, verbose=False)
            end = time.time()-start
            if solution.shape == (n-1, n//2, n, n):
                outputs.append((result, solution, end))
            elif end >= 299:
                solvers.remove(solver)
                
            print(f"solver: {solver}")
            print(f"status: {result.Solver.status}")
            print(f"time: {end}")
        
        updateSol(n, solvers, outputs, opt=True, output_dir='../../res/MIP',
                filename=f'4dArray_{n}.json')
