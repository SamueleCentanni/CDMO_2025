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
            if result == {} \
                or not int(np.sum(solution)) == n*(n - 1)//2 \
                or solution == [] \
                or (not optimization and result.Solver.termination_condition == 'aborted') \
                or (optimization and result.Problem.Upper_bound > n) \
                or solution.shape != (n-1, n//2, n, n):
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
        obj = int(result.Problem.Upper_bound) if optimization and result.Problem.Upper_bound < n else None
        optimal = (not optimization and time < 300) or (optimization and obj == 1 and time < 300)
        formatted_sol = formatted_sol if (not optimization and time < 300) or (not obj == None) else []

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

