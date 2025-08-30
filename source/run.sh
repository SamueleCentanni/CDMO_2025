#!/bin/bash

cd source
docker build -t cdmo .
docker run -v "$PWD/res:/res" cdmo

# if res/* folders are already present the mv cmds will fail
mv ./res/CP ../res
mv ./res/SAT ../res
mv ./res/SMT ../res
mv ./res/MIP ../res