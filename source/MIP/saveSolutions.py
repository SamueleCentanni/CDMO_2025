import os, json, math
import numpy as np


def saveSol(n, outputs, optimization=True, output_dir='/res/MIP', filename='data.json', update=False):
    output = {}
    if update:
        try:
            with open(os.path.join(output_dir, filename), 'r', encoding='utf-8') as f:
                output = json.load(f)
        except:
            pass
    for o in outputs:
        result, solution, time, name = o

        try:
            if result == {} or not int(np.sum(solution)) == n*(n - 1)//2 or solution == []:
                output[name] = {
                    "sol": [],
                    "time": 300,
                    "optimal": False,
                    "obj": None,
                }
                continue
        except Exception as e:
            pass

        formatted_sol = []
        for p in range(n//2):
            row = []
            for w in range(n-1):
                for i in range(n):
                    for j in range(n):
                        if solution[w, p, i, j] == 1:
                            row.append([i+1, j+1])
            formatted_sol.append(row)

        time  = math.floor(time) if time <= 300 else 300
        obj = result.Problem.Upper_bound if optimization and result.Solver.termination_condition == 'optimal' else None
        optimal = (not optimization and time < 300) or (optimization and obj == 1 and time < 300)
        formatted_sol = formatted_sol if time < 300 else []

        try:
            if formatted_sol == []  or formatted_sol[0] == [] or result.Solver.status == 'aborted':
                time = 300
                obj = None
        except:
            pass

        output[name] = {
            "sol": formatted_sol,
            "time": time,
            "optimal": optimal,
            "obj": obj,
        }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    return