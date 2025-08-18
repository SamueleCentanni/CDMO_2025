from minizinc import Instance, Model, Solver
import minizinc
from minizinc.model import Method 
import time
from datetime import timedelta
import numpy as np
import subprocess

start = time.perf_counter()

def circle_matchings(n):
    pivot, circle = n, list(range(1, n))
    weeks = n - 1
    m = {}
    for w in range(1, weeks + 1):
        ms = [(pivot, circle[w-1])]
        for k in range(1, n//2):
            i = circle[(w-1 + k) % (n-1)]
            j = circle[(w-1 - k) % (n-1)]
            ms.append((i, j))
        m[w] = ms
    return m

def generate_dzn(n, matchings, filename):
    with open(filename, 'w') as f:
        f.write(f"num_teams = {n};\n")
        f.write(f"num_weeks = {n - 1};\n")
        f.write(f"num_slots = {n // 2};\n\n")

        weeks = np.zeros((n, n), dtype=int)
        for week_num, matches in matchings.items():
            for match in matches:
                weeks[match[0] - 1, match[1] - 1] = week_num
                weeks[match[1] - 1, match[0] - 1] = week_num

        f.write("week = [|\n")
        for i in range(n):
            row = ", ".join(str(weeks[i, j]) for j in range(n))
            if i == n - 1:
                f.write(f"{row} |];\n")  
            else:
                f.write(f"{row} |\n")

def run_minizinc(model_file, data_file, solver, output_file=None):
    model = Model(model_file)
    solver = Solver.lookup(solver)
    instance = Instance(solver, model)
    instance.add_file(data_file)
    result = instance.solve(timeout=timedelta(seconds=300), method=Method.SATISFY)
    objective_value = result.objective
    if output_file:
        with open(output_file, "w") as f:
            f.write(str(result))
    
    print("Solver statistics:")
    for k, v in result.statistics.items():
        print(f"  {k}: {v}")

    return objective_value

num_teams = 8
model_file = "circle_method_SB.mzn"
dzn_file = "schedule_data.dzn"
solver = "gecode"
matchings = circle_matchings(num_teams)
generate_dzn(num_teams, matchings, dzn_file)
output_file = "schedule_output.txt"
value = run_minizinc(model_file, dzn_file, solver, output_file)

end = time.perf_counter()
print(f"Objective value: {value}")
print(f"Total execution time: {end - start:.4f} seconds")
