# Sports Tournament Scheduling Project

This project provides a comprehensive framework for solving the sports tournament scheduling problem using various computational formulations. The entire solution is packaged in a Docker container to ensure consistent and easy execution across different machines.

## Getting Started

To get started, first clone the repository from your Git provider.

```bash
git clone <repository_url>
cd <repository_name>
```

The core of the project is the `main.py` script, which serves as a command-line interface for running the various solvers. You can start the container in a few different ways, depending on your needs—from a simple, complete benchmark to a highly customized execution.

**Important**: The `run.sh` script requires execution permissions. If you encounter a Permission Denied error, run the following command once:

```bash
chmod +x run.sh
```

## How to Run the Docker Container

### Run the Full Benchmark (Recommended):

To simultaneously run all formulations, models, and problem sizes, simply use the provided `run.sh` script. This is the recommended method for a complete benchmark.

```bash
./run.sh
```

Alternatively, you can start the container manually:

```bash
docker build -t cdmo .
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py --run_all_formulations
```

### Run a Specific Formulation:

If you want to run only a specific formulation, you can call main.py directly from the Docker container. This allows you to specify the formulation (-f) and the number of teams (-n) to test.

Available Formulations:

- cp (Constraint Programming)

- sat (Boolean Satisfiability)

- smt (Satisfiability Modulo Theories)

- mip (Mixed-Integer Programming)

_Example_: Run the SAT solver for 12 teams.

```bash
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f sat -n 12
```

You can also specify a range of teams. The script will automatically test all even numbers within that range.

_Example_: Run the CP solver for a range from 6 to 18 teams.

```bash
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f cp -n 6-18
```

To run all pre-configured n values for a specific formulation, use the `--run_all_sizes` flag.

_Example_: Run all pre-configured n values for the MIP solver.

```bash
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f mip --run_all_sizes
```

### Customize the Run with Specific Flags

For more advanced usage, you can pass any model-specific flags directly to the `main.py` script. The main script will automatically forward these arguments to the correct solver.

_Example_: Run the MIP solver with the 4D array model and verbose output enabled.

```bash
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f mip -n 12 --_4D --run_decisional --verbose
```

### Run Locally (Without Docker)

While the Docker container is the recommended method for consistent execution, you can also run the solvers directly on your machine.

Navigate to the src directory and run the main.py script for the desired solver. Note that the folder structure and file paths may differ from those inside the container.

Example for the SAT solver

```bash
cd src/SAT
python3 main.py -n 12 --run_decisional
```
