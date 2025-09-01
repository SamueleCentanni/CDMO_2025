import os, json, math


def saveSol(n, outputs, opt=True, output_dir='/res/MIP', filename='data.json'):
    output = {}
    for h,o in enumerate(outputs):
        result, solution, time, name = o
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
        output[name] = {
            "sol": formatted_sol,
            "time": time if optimal else 300,
            "optimal": optimal,
            "obj": obj if opt else None,
        }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    return

def updateSol(n, outputs, opt=True, output_dir='/res/MIP', filename='data.json'):
    output = {}
    try:
        with open(os.path.join(output_dir, filename), 'r', encoding='utf-8') as f:
            output = json.load(f)
    except:
        pass
    for h,o in enumerate(outputs):
        result, solution, time, name = o
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
        output[name] = {
            "sol": formatted_sol,
            "time": time if optimal else 300,
            "optimal": optimal,
            "obj": obj if opt else None,
        }

    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, filename), 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=4)
    return
