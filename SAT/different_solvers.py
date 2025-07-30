from z3 import *
from pysat.formula import CNF
from pysat.solvers import Minisat22, Glucose3, Glucose42
import time
import multiprocessing
import traceback

# === 1. Create and Export the Model ===
def export_model_to_dimacs(solver, filename="sts_model.cnf"):
    goal = Goal()
    goal.add(solver.assertions())
    
    tactic = Then(Tactic("simplify"), Tactic("tseitin-cnf"))
    cnf_goal = tactic(goal)[0]

    with open(filename, "w") as f:
        f.write(cnf_goal.dimacs())

    print(f"CNF exported to {filename}")

# === 2. Parse DIMACS Variable Map ===
def parse_dimacs_variable_map(dimacs_file_path):
    mapping = {}
    with open(dimacs_file_path, "r") as f:
        for line in f:
            if line.startswith("c "):
                parts = line.strip().split()
                if len(parts) >= 3:
                    dimacs_var = int(parts[1])
                    z3_var = parts[2]
                    mapping[z3_var] = dimacs_var
    return mapping

# === 3. Solve with PySAT (Minisat22 / Glucose3 / Glucose4) ===
def solve_with_pysat(dimacs_path, solver_name='minisat'):
    cnf = CNF(from_file=dimacs_path)

    if solver_name == "minisat":
        SolverClass = Minisat22
    elif solver_name == "glucose3":
        SolverClass = Glucose3
    elif solver_name == "glucose4":
        SolverClass = Glucose42        
    else:
        raise ValueError(f"Unsupported solver: {solver_name}. Use 'minisat', 'glucose3', or 'glucose4'.")

    with SolverClass(bootstrap_with=cnf.clauses) as solver:
        satisfiable = solver.solve()
        model = solver.get_model() if satisfiable else None
    return satisfiable, model

# === 4. Runner in separate process ===
def pysat_runner(dimacs_path, solver_name, queue):
    try:
        satisfiable, model = solve_with_pysat(dimacs_path, solver_name)
        queue.put((satisfiable, model))
    except Exception as e:
        print("Error in PySAT solver:")
        print(traceback.format_exc())
        queue.put((False, None))

# === 5. Parse Model from PySAT to Schedule ===
def parse_model(match_vars, home_vars, model, var_map, pair_to_week):
    # Trasformazione modello: da lista di interi a dict {dimacs_idx: bool}
    dimacs_to_bool = {abs(v): (v > 0) for v in model}
    schedule = []

    for (i, j, p), z3_var in match_vars.items():
        z3_name = z3_var.decl().name()
        if z3_name in var_map:
            dimacs_idx = var_map[z3_name]
            if dimacs_to_bool.get(dimacs_idx, False):
                # Match attivo, ora capiamo chi è in casa
                home_var = home_vars[(i, j)]
                home_name = home_var.decl().name()
                home_idx = var_map.get(home_name, -1)
                is_home = dimacs_to_bool.get(home_idx, False)

                home_team = i if is_home else j
                away_team = j if is_home else i

                week = pair_to_week[(i, j)] + 1  # Umano (da 0-based a 1-based)
                schedule.append((home_team + 1, away_team + 1, week, p + 1))  # Anche team e periodo da 1-based

    return schedule

# === 6. Full Pipeline with Multiprocessing Timeout ===
def solve_sts_with_dimacs(model_creator_fn, timeout=300, solver_name="minisat"):
    start_time = time.time()
    
    print("Creating model...")
    
    solver, match_vars, home_vars, *_, pair_to_week = model_creator_fn()

    export_model_to_dimacs(solver)
    
    print("Parsing variable map...")
    var_map = parse_dimacs_variable_map("sts_model.cnf")

    print(f"Solving with PySAT ({solver_name})...")

    queue = multiprocessing.Queue()
    proc = multiprocessing.Process(target=pysat_runner, args=("sts_model.cnf", solver_name, queue))
    
    remaining_time = timeout - (time.time() - start_time) 
    
    if remaining_time <= 0:
        print("Timeout reached before starting the solver.")
        return {
            'solver': solver_name,
            'solution': None,
            'time': timeout,
            'satisfiable': False
        }

    try:
        proc.start()
        satisfiable, model = queue.get(timeout=remaining_time + 1)  
    except Exception as e:
        print(f"Timeout or error: {e}")
        satisfiable = False
        model = None
    finally:
        proc.terminate()
        proc.join()

    solve_time = time.time() - start_time
    print(f"Solve time: {solve_time:.2f}s")

    if not satisfiable or model is None:
        return {
            'solver': solver_name,
            'sol': None,
            'time': solve_time,
            'satisfiable': False
        }

    print("SAT Solution Found!")
    schedule = parse_model(match_vars, home_vars, model, var_map, pair_to_week)
    return {
        'solver': solver_name,
        'sol': schedule,
        'time': solve_time,
        'satisfiable': True
    }