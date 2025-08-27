#!/usr/bin/env python
from MIP.circleMatching import runAllCircleMatching
from MIP._4dArray import runAll4dArray
import os

if __name__ == '__main__':
    if os.path.exists('/src/MIP/gurobi.lic'):
        os.makedirs('/opt/gurobi', exist_ok=True)
        os.rename('/src/MIP/gurobi.lic', '/opt/gurobi/gurobi.lic')

    runAllCircleMatching()
    runAll4dArray()