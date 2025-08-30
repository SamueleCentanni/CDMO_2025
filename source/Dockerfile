FROM minizinc/minizinc:latest

RUN mkdir /src
# include src files
ADD ./main.py /src
ADD ./CP /src/CP
ADD ./SAT /src/SAT
ADD ./SMT /src/SMT
ADD ./MIP /src/MIP

RUN apt-get update
RUN apt-get install -y python3 python3-pip
# RUN apt-get install -y --no-install-recommends coinor-cbc coinor-libcbc-dev glpk-utils && rm -rf /var/lib/apt/lists/*

# Create and use a Python virtual environment for package installation
RUN pip3 install --break-system-packages --no-cache-dir minizinc numpy pyomo gurobipy z3-solver

# Use the virtual environment's Python for running the main script
CMD ["python3", "/src/main.py", "-f", "all", "-n", "all"]

