# Docker execution

The docker container can be run in 3 ways:

1. all formulations, models and num of teams simultaneously (recommended)
2. a single formulation with the possibility of managing the num of teams but not the parameters and models
3. customize the run command as needed by appending it to the docker command
4. (in case you need to ru nit without docker it is still possible: invocke the main.py inside each folder, but keep in mind that the folder structure in the container is different so somthing might change)

## 1.

To solve everything all together just run the `run.sh` script or:

```
cd source
docker build -t cdmo .
ocker run -v "$PWD/res:/res" cdmo python3 /src/main.py --run_all_formulations
mv ./res/CP ../res
mv ./res/SAT ../res
mv ./res/SMT ../res
mv ./res/MIP ../res
```

## 2.

To solve for a single formulation copy the following code and change FORMULATION ot one of [cp,sat,smt,mip] and N to a range or a number.

```
cd source
docker build -t cdmo .
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f FORMULATION -n N
mv ./res/MIP ../res
```

# 3.

If more customization is needed, follow the instrucitons for #2 and modify the command following "docker run -v "$PWD/res:/res" cdmo"
for a complete reference of possibility refer to the command line argument helpers.
