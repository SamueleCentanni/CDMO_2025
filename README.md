# Sports Tournament Scheduling (STS) Project

**Combinatorial Decision Making and Optimization**
*University of Bologna - September 2025*

**Authors:**
* Samuele Centanni
* Tomaž Cotič
* Mattia Lodi
* Artem Uskov

---

## Project Overview

This project addresses the **Sports Tournament Scheduling (STS)** problem, which involves creating a compact round-robin schedule for $n$ teams over $n-1$ weeks. The goal is to satisfy the fundamental constraints of a tournament while optimizing the fairness of the schedule by balancing home and away games.

### The Objective
The core objective across all models is to **minimize the maximum absolute difference** between the number of home and away matches played by any team:

$$O = \max_{t \in T} |H_t - A_t|$$

Initially, we considered an alternative formulation based on the sum of imbalances, but empirical evaluation showed that minimizing the maximum imbalance consistently produced significantly better results across all techniques.

---

## Methodology & Models

All approaches leverage a **Circle Method pre-solving step**. This technique fixes the weekly pairings in advance, allowing the solvers to focus purely on optimizing the assignment of **periods** (time slots) and **venues** (Home/Away).

### 1. Constraint Programming (CP)
* **Implementation:** MiniZinc with Gecode and Chuffed solvers.
* **Key Features:** Uses global constraints like `count_geq` to ensure teams play at most twice in the same period.
* **Symmetry Breaking:** Constraints fix the slots of the first team and the home/away pattern of Team 1, significantly pruning the search space.

### 2. Boolean Satisfiability (SAT)
* **Implementation:** Python with Z3 API.
* **Encodings:** Comparison of Pairwise, Bitwise, Sequential, Heule, and Totalizer encodings for cardinality constraints.
* **Performance:** The **Heule + Totalizer** encoding combination proved most efficient for scalability.

### 3. Satisfiability Modulo Theories (SMT)
* **Implementation:** Python with Z3.
* **Logic:** Modeled using Linear Integer Arithmetic (LIA) extended with pseudo-Boolean constraints.
* **Efficiency:** Circular matching pre-solving allowed us to solve instances with up to 20 teams, whereas earlier models with more decision variables were more limited.

### 4. Mixed Integer Programming (MIP)
* **Implementation:** Pyomo with Gurobi, Cbc, and Glpk solvers.
* **Models:** A 4D array baseline was compared against a **Circle Matching (CM)** model.
* **Findings:** Gurobi consistently performed best, following the usual hierarchy of commercial solvers over open-source alternatives like Cbc or Glpk.

---

## Summary of Results

* **Scalability:** The most effective approaches scaled up to **20 teams** within the 300s timeout.
* **Optimization:** The optimal objective value (Max Imbalance = 1) was achieved in all successfully solved instances.
* **Symmetry Breaking:** Essential across all paradigms. It enabled CP to solve $n=16$ to optimality and provided significant speedups in SAT and SMT.

---

## Getting Started & Usage

This project is packaged in a Docker container to ensure consistent and easy execution across different machines.

### Prerequisites
* Docker installed on your machine.
* Git.

### Installation
Clone the repository:

``
git clone <repository_url>
cd <repository_name>
``

**Important**: The run.sh script requires execution permissions:

``
chmod +x run.sh
``

## How to Run the Docker Container

### 1. Run the Full Benchmark (Recommended)
To simultaneously run all formulations, models, and problem sizes:

``
./run.sh
``

Alternatively, launch it manually:

``
docker build -t cdmo .
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py --run_all_formulations
``

### 2. Run a Specific Formulation
Execute main.py directly in the container specifying the formulation (-f) and the number of teams (-n).

**Example SAT (12 teams, all encodings):**

``
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f sat -n 12 --all
``

**Example CP (range 6-18 teams):**

``
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f cp -n 6-18 --all
``

### 3. Customize the Run
You can pass model-specific flags directly to the desired model.

**Example MIP with 4D model and verbose output:**

``
docker run -v "$PWD/res:/res" cdmo python3 /src/main.py -f mip -n 12 --_4D --run_decisional --verbose
``

### 4. Run Locally (No Docker)
Navigate to the specific formulation folder in src.

**Example SAT:**

``
cd src/SAT
python3 main.py -n 12 --run_decisional --all
``
