# Docker execution

## Exec all
To solve the problem for all the instances and models with docker just run the ```run.sh``` script or:
```
cd source
docker build -t cdmo .
docker run -v "$PWD/res/MIP:/res/MIP" cdmo
mv ./res/MIP ../res
```

## Excec MIP
For the MIP formulation, the best modelling is in circleMatching.py
To solve the problem only for the MIP formulation run: