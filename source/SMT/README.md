# CDMO_2025
Combinatorial Decision Making and Optimization to solve the Sport Tournament Scheduling (STS)

## SMT 

### Usage:
python decisional.py <n> <approach_base> [--sb_disabled]

approach_base is just the name of the approach string displayed in json
--sb_disabled flag will disable symmetry breaking, otherwise enabled by default

### Examples:

1.
python decisional.py 16 z3_decisional_but_also_optimal_by_graph_theory 
will run decisional version for n=16
and append the results to json in res/SMT
where z3_decisional_but_also_optimal_by_graph_theory is just the name of the approach in json
add --sb_disabled flag to disable symmetry breaking

2.
python optimal.py 16 z3_optimal
will run decisional version for n=16
and append the results to json in res/SMT

usually both versions can do up to n=20 in less than 5 minutes

3.
python solution_checker.py res/SMT
would run professor's checker to validate the satisfaction
of all the constraints, but not optimality

4.to check optimality we have our own checker
python check_optimality.py res\SMT