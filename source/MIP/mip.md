# MIP
The MIP formulation was developed with pyomo, a python library for writing solver independant models.
Two models were developed: a base version composed of a 4d array with symmetry breaking and implied constraints and a better one, optimizing the number of variables featuring circle matching.


# 4d array
This model is the simplest possible implementaiton of the STS problem, developed only for comparison as it's not nearly as efficent as the next one.
## variables
### decision
The only variable is X, a 4d array n-1 x n/2 x n x n of binary values, where each cell represent a match, described as a combination of week, period, team1 and team2. The first team is the one playing home.
### optimization
See the following section as the optimization is implemented in the same way.
## constraints
### necessary
1. one_match_per_team: each team plays exactly n-1 matches
2. symmetry: only one of (w,p,i,j) or (w,p,j,i) can be played
3. one_match_per_week: each team plays once every week
4. max_one_per_period_per_week: each match of every week is in at most one period
5. max_one_game_per_match: each match is played in at most one week/period slot
6. max_two_matches_per_period: a temas plays at most twice in the same period
7. one_game_per_team_per_week: each team plays one game per week
8. one_match_per_period_per_week: one match per week/period slot
### implied
1. total_matches
2. no_self_match
### symmetry breaking
1. fix_first_week_rule
2. fix_team0_schedule_rule
### objective
See the following section.

# circle matching
Model using the circle matching schedule for presolving.
## variables
### decision
Two variables are used:
1. Y a matrix of (n-1)*(n//2) x (n*(n - 1)//2) binary values, the most strict possible formulation in order to minimize the variable count. The indices of the matrix are couples (w,p) and (i,j) where i<j
2. H a binary array of length (n*(n - 1)//2), indicating for each match (i,j) if the team i plays home or away  
The domains are [0,1] to ease the constraints formualtion and to improve the search speed.
### implied
The implied constraint necessitates a variable Zteam that keeps track of which team played on which period.
### optimization

## constraints
... 
In this particular model the addition of symmetry breaking constraints did't improve the results, as circle matching already breaks some symmetries, this is why they are not included.
### circle matching
Once the week/match schedule has been computed, to be effective it needs to be added as a constraint:
we set a constraint for each scheduled match imposing for each w,p,m, Y <= circle matching
### necessary
1. one_match_per_period_per_week_rule: each week/period solt needs to have one match scheduled
2. match_scheduled_once_rule: each match can be scheduled once for all week/period solts 
3. max_team_match_period: a team k can play at most twice in the same period
### implied
Especially useful in an optimization environment, this constraint aims to spread the matches of a team in different periods over the scheduling, to get a more balanced result. It also help with symmetry breaking.
### objective
The home_games and away_games are meant to populate the variables Home and Away with the right values.
balance_max sets both Home-Away <= Z and Away-Home <= Z for every team, to implement the objective.

# solvers
The results were obtained by running the models for 3 different solvers: cbc, glpk and guroby. cbc and glpk are open source solvers while gurobi is proprietary, used under an accademic licence.