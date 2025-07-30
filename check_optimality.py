import os
import json
import glob
from collections import defaultdict

def check_jsons(folder):
    """
    For each JSON file named '<n>.json' in folder, extract n from filename,
    compute sum of |home-away difference| per team, and report validity if sum == n.
    """
    for path in glob.glob(os.path.join(folder, '*.json')):
        name = os.path.splitext(os.path.basename(path))[0]
        try:
            n = int(name)
        except ValueError:
            print(f"Skipping file with invalid name: {os.path.basename(path)}")
            continue
        with open(path) as f:
            data = json.load(f)
        print(f"File: {os.path.basename(path)} (n={n})")
        for approach, info in data.items():
            sol = info.get('sol', [])
            home_counts = defaultdict(int)
            away_counts = defaultdict(int)
            if sol:
                periods = len(sol)
                weeks = len(sol[0])
                for p in range(periods):
                    for w in range(weeks):
                        home, away = sol[p][w]
                        home_counts[home] += 1
                        away_counts[away] += 1
            sum_diff = sum(abs(home_counts[t] - away_counts[t]) for t in home_counts)
            valid = (sum_diff == n)
            status = 'VALID' if valid else 'INVALID'
            print(f"  {approach}: sum_diff={sum_diff} -> {status}")

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <json_folder>")
        sys.exit(1)
    folder = sys.argv[1]
    check_jsons(folder)
