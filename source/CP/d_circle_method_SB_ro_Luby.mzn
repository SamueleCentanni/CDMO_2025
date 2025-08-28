include "globals.mzn";
include "chuffed.mzn";

int: num_teams;
int: num_weeks;
int: num_periods;
array[Teams, Teams] of Weeks: week;

set of int: Teams = 1..num_teams;
set of int: Weeks = 0..num_weeks;
set of int: Periods = 0..num_periods;

% Decision variables
array[Teams, Teams] of var Periods: period;
array[Teams, Teams] of var bool: home;

% enforce symmetry of the tables
constraint forall(i,j in Teams where i!=j)(period[i,j]!=0);
constraint forall(i in Teams) (period[i,i] == 0);
constraint forall(i,j in Teams where i<j)(period[i,j] == period[j,i]);
constraint forall(i,j in Teams where i<j) (home[j,i] == 1- home[i,j]);

% Each team plays at most twice in the same period
constraint forall(t in Teams, p in Periods)(count_geq([period[t,j] | j in Teams], p, 2));
   
% Consistent fil between week and slot - each week exactly n/2 matches
constraint forall(w in 1..num_weeks, p in 1..num_periods )(   sum([bool2int(week[i,j] == w /\ period[i,j] == p) | i,j in Teams where i < j]) = 1);


% SYMMETRY BREAKING
% fix slots of the first team
constraint increasing(period[1,..]);

% fix the games team 1 plays at home and those it plays away
constraint forall(w in 1..(num_teams div 2)) (
  home[1, w + 1] == 1
);
constraint forall(w in ((num_teams div 2) + 1)..num_teams-1) (
  home[1, w + 1] == 0
);

solve::seq_search([
  int_search([period[i,j] | i,j in Teams where i<j], random_order, indomain_split), 
  int_search([home[i,j] | i,j in Teams where i<j], random_order, indomain_split)]) :: restart_luby(50) satisfy;