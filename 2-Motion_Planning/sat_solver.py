"""
3-CNF-SAT Phase Transition Experiment
"""

import random
import matplotlib.pyplot as plt


def generate(n, m):
    """
    Generate a random 3-CNF formula.

    Parameters:
        n: number of variables (1 to n)
        m: clause-to-variable ratio

    Returns:
        List of clauses, where each clause is a tuple of 3 literals.
        A literal is a positive int (variable) or negative int (negated variable).
    """
    num_clauses = int(n * m)
    formula = []

    for _ in range(num_clauses):
        clause = []
        for _ in range(3):
            # Choose a random variable (1 to n)
            var = random.randint(1, n)
            # Randomly negate (50% chance)
            if random.random() < 0.5:
                var = -var
            clause.append(var)
        formula.append(tuple(clause))

    return formula


def solve(formula):
    """
    Solve a 3-CNF formula using backtracking with unit propagation.

    Parameters:
        formula: list of clauses (each clause is a tuple of literals)

    Returns:
        True if satisfiable, False if unsatisfiable
    """
    # Convert to list of sets for easier manipulation
    clauses = [set(clause) for clause in formula]
    assignment = {}
    return _backtrack(clauses, assignment)


def _backtrack(clauses, assignment):
    """Recursive backtracking with unit propagation."""
    # Unit propagation loop
    changed = True
    while changed:
        changed = False

        # Check for empty clause (conflict)
        for clause in clauses:
            if len(clause) == 0:
                return False

        # Find and propagate unit clauses
        for clause in clauses:
            if len(clause) == 1:
                lit = next(iter(clause))
                clauses, assignment = _propagate(clauses, assignment, lit)
                changed = True
                break

    # Check for empty clause after propagation
    for clause in clauses:
        if len(clause) == 0:
            return False

    # All clauses satisfied
    if len(clauses) == 0:
        return True

    # Choose an unassigned variable from the first clause
    lit = next(iter(clauses[0]))
    var = abs(lit)

    # Try assigning True (positive literal)
    new_clauses = [clause.copy() for clause in clauses]
    new_assignment = assignment.copy()
    new_clauses, new_assignment = _propagate(new_clauses, new_assignment, var)
    if _backtrack(new_clauses, new_assignment):
        return True

    # Try assigning False (negative literal)
    new_clauses = [clause.copy() for clause in clauses]
    new_assignment = assignment.copy()
    new_clauses, new_assignment = _propagate(new_clauses, new_assignment, -var)
    return _backtrack(new_clauses, new_assignment)


def _propagate(clauses, assignment, literal):
    """Propagate a literal assignment through the formula."""
    var = abs(literal)
    value = literal > 0
    assignment[var] = value

    new_clauses = []
    for clause in clauses:
        if literal in clause:
            # Clause is satisfied, remove it
            continue
        elif -literal in clause:
            # Remove the false literal from clause
            new_clause = clause.copy()
            new_clause.discard(-literal)
            new_clauses.append(new_clause)
        else:
            # Clause unchanged
            new_clauses.append(clause)

    return new_clauses, assignment


def run_experiment(n=100, m_start=1.0, m_end=8.0, m_step=0.25, trials=25):
    """
    Run the phase transition experiment.

    Parameters:
        n: number of variables
        m_start: starting clause-to-variable ratio
        m_end: ending clause-to-variable ratio
        m_step: step size for m
        trials: number of trials per m value

    Returns:
        List of (m, fraction_satisfiable) tuples
    """
    results = []

    # Generate list of m values
    m_values = []
    m = m_start
    while m <= m_end + 0.001:  # Small epsilon for floating point
        m_values.append(round(m, 2))
        m += m_step

    total_points = len(m_values)
    print(f"Running experiment: n={n}, {trials} trials per m value")
    print(f"m range: {m_start} to {m_end} (step {m_step})")
    print(f"Total: {total_points} data points, {total_points * trials} solver calls")
    print()

    for i, m in enumerate(m_values):
        sat_count = 0
        n_clauses = int(n * m)

        for trial in range(trials):
            formula = generate(n, m)
            if solve(formula):
                sat_count += 1

        fraction = sat_count / trials
        results.append((m, fraction))
        print(f"m={m:.2f} ({n_clauses} clauses): {sat_count}/{trials} SAT ({fraction:.0%})")

    return results


def plot_results(results, n=100, trials=40, output_file="sat_phase_transition.png"):
    """
    Plot the phase transition results.

    Parameters:
        results: list of (m, fraction_satisfiable) tuples
        n: number of variables (for title)
        trials: number of trials per point (for title)
        output_file: path to save the PNG file
    """
    m_values = [r[0] for r in results]
    sat_fractions = [r[1] for r in results]

    plt.figure(figsize=(10, 6))
    plt.plot(m_values, sat_fractions, 'b-o', linewidth=2, markersize=6)

    plt.xlabel('Clause-to-Variable Ratio (m)', fontsize=12)
    plt.ylabel('Fraction Satisfiable', fontsize=12)
    plt.title(f'3-SAT Phase Transition (n={n} variables, {trials} trials per point)', fontsize=14)

    plt.xlim(1.0, 8.0)
    plt.ylim(0.0, 1.05)
    plt.grid(True, alpha=0.3)

    # Mark the theoretical threshold (~4.26)
    plt.axvline(x=4.26, color='r', linestyle='--', alpha=0.7, label='Critical ratio (~4.26)')
    plt.legend()

    plt.tight_layout()
    plt.savefig(output_file, dpi=150)
    plt.close()

    print(f"\nPlot saved to {output_file}")


if __name__ == '__main__':
    # Full experiment: n=100, m=1.0 to 8.0, step 0.25, 25 trials
    print("=" * 50)
    print("3-SAT Phase Transition Experiment")
    print("=" * 50)

    random.seed(42)
    results = run_experiment(n=100, m_start=1.0, m_end=8.0, m_step=0.25, trials=100)

    plot_results(results, n=100, trials=100, output_file="sat_phase_transition.png")
