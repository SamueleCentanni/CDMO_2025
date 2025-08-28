# Docker execution

## All
To solve the problem for all the instances and models with docker just run the ```run.sh``` script or:
```
cd source
docker build -t cdmo .
docker run -v "$PWD/res/MIP:/res/MIP" cdmo
mv ./res/MIP ../res
```

## MIP
For the MIP formulation, the best result are obtained with the gurobi solver, which requires a license
To solve the problem only for the MIP formulation:
- copy the license file ```gurobi.ilc``` into the source/MIP directory (otherwise the default open-source solvers will be used)
- run: 
```
cd source
docker build -t cdmo .
docker run -v "$PWD/res/MIP:/res/MIP" cdmo python /src/main.py -f mip -n 10
mv ./res/MIP ../res
```
the argument -f mip to choose the MIP formulation and -n to specify an n (otherwise all ns will be tried)