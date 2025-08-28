FROM python:3.13-slim

RUN mkdir /src
# include src files
ADD ./main.py /src
ADD ./SAT /src/SAT
ADD ./MIP /src/MIP
ADD ../res /res

RUN apt-get update && apt-get install -y --no-install-recommends coinor-cbc coinor-libcbc-dev glpk-utils && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir pyomo numpy gurobipy z3-solver

# python /src/main.py -f all -n all
CMD ["python", "/src/main.py", "-f", "all", "-n", "all"] 