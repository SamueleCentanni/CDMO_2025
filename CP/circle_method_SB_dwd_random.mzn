include "globals.mzn";

int: num_teams;
int: num_weeks;
int: num_slots;
array[Teams, Teams] of Weeks: week;

set of int: Teams = 1..num_teams;
set of int: Weeks = 0..num_weeks;
set of int: Slots = 0..num_slots;

% Decision variables
array[Teams, Teams] of var Slots: slot;
array[Teams, Teams] of var bool: home;

% enforce symmetry of the tables
constraint forall(i,j in Teams where i!=j)(slot[i,j]!=0);
constraint forall(i in Teams) (slot[i,i] == 0);
constraint forall(i,j in Teams where i<j)(slot[i,j] == slot[j,i]);
constraint forall(i,j in Teams where i<j) (home[j,i] == 1- home[i,j]);

% Each team plays at most twice in the same period
constraint forall(t in Teams, s in Slots)(count_geq([slot[t,j] | j in Teams], s, 2));
   
% Consistent fil between week and slot - each week exactly n/2 matches
constraint forall(w in 1..num_weeks, s in 1..num_slots )(   sum([bool2int(week[i,j] == w /\ slot[i,j] == s) | i,j in Teams where i < j]) = 1);

% SYMMETRY BREAKING
% fix slots of the first team
constraint increasing(slot[1,..]);

% fix the games team 1 plays at home and those it plays away
constraint forall(w in 1..(num_teams div 2)) (
  home[1, w + 1] == 1
);
constraint forall(w in ((num_teams div 2) + 1)..num_teams-1) (
  home[1, w + 1] == 0
);

% OPTIMIZATION
array[Teams] of var 0..num_weeks: home_count;
array[Teams] of var 0..num_weeks: away_count;

constraint forall(t in Teams) (
    home_count[t] = sum([bool2int(home[t,j] == 1) | j in Teams where j != t]));
constraint forall(t in Teams)(
    away_count[t] = sum([bool2int(home[t,j] == 0) | j in Teams where j != t])
  );
  
array[Teams] of var 0..num_weeks: imbalance;
constraint forall(t in Teams) (imbalance[t] = abs(home_count[t] - away_count[t]));

var int: total_imbalance = max(imbalance);
constraint total_imbalance >= 1;
constraint total_imbalance <= num_teams;

solve :: int_search([slot[i,j] | i,j in Teams where i<j] ++ [home[i,j] | i,j in Teams where i<j], dom_w_deg, indomain_random) minimize total_imbalance;