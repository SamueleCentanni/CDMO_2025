import os
import json
import math



def print_weekly_schedule(match_list, num_teams):
    '''
        Tournament Scheduler
    '''
    num_weeks = num_teams - 1
    num_periods = num_teams // 2

    print("\n--- Sport Tournament Scheduler ---")
    print(f"Number of Teams: {num_teams}")
    print(f"Number of Weeks: {num_weeks}")
    print(f"Periods per Week: {num_periods}")
    print("---------------------------\n")
    
    if match_list is None:
        print("No solution was found")
        return

    schedule = {}
    
    if match_list is not None:
        for i, j, w, p in match_list:
            schedule[(w - 1, p - 1)] = (i - 1, j - 1) # from 1-based to 0-based

        for w_idx in range(num_weeks):
            print(f"Week {w_idx + 1}:")
            for p_idx in range(num_periods):
                match = schedule.get((w_idx, p_idx))
                if match:
                    home_team_idx, away_team_idx = match
                    # Team i (i=0,1,..) becomes Team i+1 
                    print(f"  Period {p_idx + 1}: Team {home_team_idx + 1} (Home) vs Team {away_team_idx + 1} (Away)")
                else:
                    print(f"  Period {p_idx + 1}: [No Programmed Matches]")
            print()
    

    print("--- END SCHEDULE ---\n")


def convert_to_matrix(n, solution):
    num_periods = n // 2
    num_weeks = n - 1
    matrix = [[None for _ in range(num_weeks)] for _ in range(num_periods)]
    for h, a, w, p in solution:
        matrix[p - 1][w - 1] = [h, a]
    return matrix

def save_results_as_json(n, results, output_dir="../res/SAT"):
    os.makedirs(output_dir, exist_ok=True)
    
    json_path = os.path.join(output_dir, f"{n}.json")
    
    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            json_obj = json.load(f)
    else:
        json_obj = {}
    
    for method, result in results.items():
        runtime = result.get("time", 300.0)
        time_field = 300 if not result.get("optimal") else math.floor(runtime)
        sol = result.get("sol")
        matrix = convert_to_matrix(n, sol) if sol else []
        json_obj[method] = {
            "time": time_field,
            "optimal": result.get("optimal"),
            "obj": result.get("obj"),
            "sol": matrix
        }
    
    with open(json_path, "w") as f:
        json.dump(json_obj, f, indent=1)
        
        
        

def save_stats_as_json(n, results, output_dir="./plots/plot"):
    os.makedirs(output_dir, exist_ok=True)

    json_obj = {}
    for method, result in results.items():
        runtime = result.get("time", 300.0)
        time_field = 300 if not result.get("optimal") else math.floor(runtime)

        json_obj[method] = {
            "time": time_field,
            "conflicts": result.get("conflicts"),
            "max_memory": result.get("max_memory"),
            "mk_bool_var": result.get("mk_bool_var")
        }
    
    json_path = os.path.join(output_dir, f"{n}.json")
    with open(json_path, "w") as f:
        json.dump(json_obj, f, indent=1)


    

def save_compare_solver_result(n, solver_name, result, output_dir="./plots/compare_solvers"):
    os.makedirs(output_dir, exist_ok=True)

    json_path = os.path.join(output_dir, f"{n}.json")

    if os.path.exists(json_path):
        with open(json_path, "r") as f:
            json_obj = json.load(f)
    else:
        json_obj = {}

    if result is None:
        time_field = 300
    else:
        runtime = result.get("time", 300.0)
        time_field = math.floor(runtime) if result.get("sol", False) else 300

    json_obj[solver_name] = {
        "time": time_field
    }

    with open(json_path, "w") as f:
        json.dump(json_obj, f, indent=2)

    print(f"Saved/updated {solver_name} result in {json_path}")