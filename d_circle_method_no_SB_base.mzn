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
constraint forall(i in Teams) (slot[i,i] == 0);
constraint forall(i,j in Teams where i!=j)(slot[i,j]!=0);
constraint forall(i,j in Teams where i!=j)(slot[i,j] == slot[j,i]);
constraint forall(i,j in Teams where i!=j) (home[j,i] == 1- home[i,j]);

% Each team plays at most twice in the same period
%constraint forall(t in Teams, s in Slots)(sum([bool2int(slot[t,j] == s) | j in Teams where t != j]) <= 2);

%constraint forall(i in Teams)(global_cardinality([slot[i,j]|j in Teams],[s |s in Slots], [1 | s in Slots], [2 | s in Slots]));

constraint forall(t in Teams, s in Slots)(count_geq([slot[t,j] | j in Teams], s, 2));

% Consistent fil between week and slot - each week exactly n/2 matches.
constraint forall(w in 1..num_weeks, s in 1..num_slots )(   sum([bool2int(week[i,j] == w /\ slot[i,j] == s) | i,j in Teams where i < j]) = 1);

%Alldifferent worsenes the performance
%constraint forall(w in 1..num_weeks) (alldifferent([slot[i,j] | i,j in Teams where i<j /\ week[i,j] == w]));

solve satisfy;