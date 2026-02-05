# 3-CNF-SAT Phase Transition Experiment Plan

## Overview
Create an experiment to visualize the phase transition behavior of random 3-CNF-SAT, showing how satisfiability drops sharply around the critical clause-to-variable ratio (~4.26).

## Final Experiment Parameters
- **Variables**: n = 100 (fixed)
- **Clause-to-variable ratio**: m = 1.0 to 8.0, step 0.25 (29 values)
- **Clauses per instance**: 100 × m (e.g., m=4 → 400 clauses)
- **Trials per m value**: 25
- **Total solver calls**: 725

## File to Create
`/workspaces/CMS_430/3-SAT_Phase_Transition/sat_solver.py`

---

## Phase 1: Randomized Instances Generator

### Function: `generate(n, m)`
- **n**: number of variables
- **m**: clause-to-variable ratio
- **Returns**: formula that solver can use as input

### Generation Rules
- Number of clauses = `int(n * m)`
- Each clause has exactly 3 literals
- Each literal chosen randomly from all variables and their negations
- **Sample with replacement** - no limit on how many times a variable appears
- A literal is either `+var` (positive) or `-var` (negated), chosen 50/50

### Data Structure
```python
# Literal: positive int = variable, negative int = negated
# Clause: tuple of 3 literals (allows duplicates from sampling)
# Formula: list of clauses
formula = [
    (1, -3, 5),    # x1 OR NOT x3 OR x5
    (-2, 2, 4),    # NOT x2 OR x2 OR x4 (possible with replacement)
    ...
]
```

### Testing the Generator (before proceeding)
1. **Small manual test** (n=3, m=2 → 6 clauses):
   - Verify exactly 6 clauses generated
   - Verify each clause has 3 literals
   - Verify literals are in range [-n, -1] ∪ [1, n]

2. **Automated validation** (n=10, m=5 → 50 clauses):
   - Check clause count matches expected
   - Check all literals are valid variable references
   - Print sample output for visual inspection

---

## Phase 2: SAT Solver

### Function: `solve(formula)`
- **Input**: formula from generator (list of clauses)
- **Output**: `True` (satisfiable) or `False` (unsatisfiable)
- No need to return actual assignment (but useful for testing)

### Implementation: Backtracking with Unit Propagation
1. **Unit propagation**: If a clause has only 1 unassigned literal, that literal must be true
2. **Backtracking**: Try assigning True/False to unassigned variables
3. **Early termination**: Return False immediately if empty clause found

### Algorithm Sketch
```
solve(formula):
    clauses = copy formula as mutable sets
    assignment = {}
    return backtrack(clauses, assignment)

backtrack(clauses, assignment):
    # Propagate unit clauses
    while unit clause exists:
        propagate that literal
        if empty clause: return False

    if no clauses left: return True

    # Pick unassigned variable, try both values
    var = pick_variable(clauses)
    for value in [True, False]:
        if backtrack(with var=value): return True
    return False
```

### Testing the Solver (before proceeding)
1. **Manual small tests**:
   - `[(1, 2, 3)]` → SAT (any assignment with x1 or x2 or x3 true)
   - `[(1,), (-1,)]` → UNSAT (contradiction)
   - `[(1, 2, 3), (-1, -2, -3)]` → SAT

2. **Known instances**: Test on a few hand-crafted SAT/UNSAT cases

3. **Random small scale**: Generate n=10, m=3 instances, verify solver terminates

---

## Phase 3: Experiment Harness

### Function: `run_experiment()`
Calls generator and solver in a loop for increasing values of m.

```python
def run_experiment():
    n = 100
    trials = 25
    results = []  # (m, fraction_sat)

    for m in [1.0, 1.25, 1.5, ..., 8.0]:
        sat_count = 0
        for trial in range(trials):
            formula = generate(n, m)
            if solve(formula):
                sat_count += 1
        fraction = sat_count / trials
        results.append((m, fraction))
        print(f"m={m:.2f}: {fraction:.0%} satisfiable")

    return results
```

### Progress Output (minimal during real experiment)
```
m=1.00: 100% satisfiable
m=1.25: 100% satisfiable
...
m=4.25: 48% satisfiable
...
m=8.00: 0% satisfiable
```

---

## Phase 4: Plotting

### Function: `plot_results(results)`
- X-axis: clause-to-variable ratio m (1.0 to 8.0)
- Y-axis: fraction satisfiable (0.0 to 1.0)
- Mark theoretical threshold ~4.26
- Save as PNG

---

## Implementation Order

1. **Implement `generate(n, m)`** → Test thoroughly
2. **Implement `solve(formula)`** → Test on small/known instances
3. **Implement `run_experiment()`** → Test with small n first (n=20)
4. **Implement `plot_results()`** → Generate final plot
5. **Run full experiment** with n=100

## Reference Files
- `/workspaces/CMS_430/2-Motion_Planning/motion.py` - coding style

## Verification Checklist
- [ ] Generator produces correct clause counts
- [ ] Generator literals are valid (in range, 3 per clause)
- [ ] Solver returns True for known SAT instances
- [ ] Solver returns False for known UNSAT instances
- [ ] Small-scale experiment shows expected S-curve trend
- [ ] Full experiment completes and produces plot
