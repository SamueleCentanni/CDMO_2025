#!/bin/bash

cd source
docker build -t cdmo .
docker run -v "$PWD/res/MIP:/res/MIP" cdmo
mv ./res/MIP ../res