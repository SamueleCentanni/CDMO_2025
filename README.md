# 🏆 Sport Tournament Scheduling with Z3

This repository provides an implementation of the **Sport Tournament Scheduling (STS)** problem using the Z3 SMT solver. It supports a variety of constraint encodings and includes both **decisional** and **optimization** solving modes.

---

## 📦 Features

- 📌 Supports **Exactly-One** encodings:

  - `np`: Naive Pairwise
  - `bw`: Binary Encoding
  - `seq`: Sequential Encoding
  - `heule`: Heule's Recursive Encoding

- 📌 Supports **At-Most-K** encodings:

  - `np`: Naive Pairwise
  - `seq`: Sequential Counter
  - `totalizer`: Totalizer Tree Encoding

- ✅ Fixed calendar generation via the **Circle Method**
- 🧩 Symmetry breaking to reduce the search space
- 🔎 Both **optimization** (MinMax imbalance) and **decisional** (find any solution) modes
- 📄 JSON output for result storage and analysis

---

## ⚙️ Usage

### Command-line Example

```bash
python script.py \
  --run_optimization \
  --exactly_one_encoding heule \
  --at_most_k_encoding totalizer \
  -n 4 6 8 \
  --sb \
  --timeout 300 \
  --save_json
```

### Arguments

| Argument                 | Description                                                     |
| ------------------------ | --------------------------------------------------------------- |
| `-n` / `--n_teams`       | Number(s) of teams, e.g., `4`, `6-12` (even only)               |
| `--timeout`              | Timeout in seconds (default: 300)                               |
| `--exactly_one_encoding` | Method for Exactly-One constraints (`np`, `bw`, `seq`, `heule`) |
| `--at_most_k_encoding`   | Method for At-Most-K constraints (`np`, `seq`, `totalizer`)     |
| `--all`                  | Run predefined combinations of encodings                        |
| `--run_decisional`       | Solve in decisional mode (check feasibility)                    |
| `--run_optimization`     | Solve in optimization mode (minimize home/away imbalance)       |
| `--max_diff`             | Max allowed imbalance for decisional mode                       |
| `--sb` / `--no-sb`       | Enable/disable symmetry breaking                                |
| `--save_json`            | Save results as JSON files in `../res/SAT`                      |
| `--verbose`              | Print detailed logs                                             |

---

## 📊 Output

- 🖨️ **Human-readable schedule** printed to console
- 📁 **JSON files** with:
  - `sol`: schedule matrix
  - `obj`: objective value (MinMax imbalance)
  - `optimal`: whether proven optimal
  - `time`: time taken
  - Solver statistics: conflicts, memory, etc.

---

## 📘 Model Description

### Problem

- Schedule a **round-robin tournament** for `n` teams (even).
- Each team plays all others exactly once.
- Matches must be assigned to one of `n/2` periods in `n-1` weeks.
- Respect max home/away imbalance (`max_diff_k`).

### Constraints

- Each match assigned to **exactly one** period
- Each period in a week has **exactly one** match
- Each team appears **at most twice** in the same period (global)
- **Home/away imbalance** limited by `max_diff_k`
- Optional symmetry breaking:
  - Fix a match in week 0
  - Alternate home/away for Team 0
  - Lexicographic ordering in week 0

---

## 📚 Encodings Implemented

### Exactly-One Encodings

- **Naive Pairwise (np)**: Pairwise mutual exclusion
- **Binary (bw)**: Binary auxiliary variables
- **Sequential (seq)**: Using auxiliary sequential bits
- **Heule**: Recursive grouping + auxiliary variables

### At-Most-K Encodings

- **Naive Pairwise (np)**: Pairwise for k+1 combinations
- **Sequential (seq)**: Sequential counter using auxiliary variables
- **Totalizer**: Tree-merge counters with propagation constraints

---

## 🧪 Benchmarks

You can test various encoding combinations using `--all`, which evaluates the following:

| Exactly-One | At-Most-K   |
| ----------- | ----------- |
| `np`        | `np`        |
| `heule`     | `seq`       |
| `heule`     | `totalizer` |

---

## 📁 Output Example

Example JSON output structure:

```json
{
  "heule_seq": {
    "time": 27,
    "optimal": true,
    "obj": 1,
    "sol": [[[1,2], [3,4], ...], [...]],
    "max_diff": 1,
    "restarts": 12,
    "conflicts": 489,
    "mk_bool_var": 2048,
    "max_memory": 13.7
  }
}
```

---

## 🔍 Notes

- `n` must be **even**.
- The solver uses Z3 with `random_seed=42` for determinism.
- The calendar is **fixed** using the circle method (only periods and home/away need assignment).

---

## 📄 License

MIT License.

---

## 🙋‍♂️ Authors

Developed as part of a project on **Combinatorial Decision Making**.

---

Feel free to contribute, raise issues, or suggest improvements!
