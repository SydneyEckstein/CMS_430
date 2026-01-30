"""
Compare BFS and IDDFS algorithms for the Lights Out puzzle.

This script runs both algorithms on progressively larger grids and
generates comparison graphs for nodes created and nodes expanded.

DSM and Claude, 2026
"""

import time
import matplotlib.pyplot as plt

# Import the solver functions from the other modules
from lights_out_bfs import solve_lights_out_bfs
from lights_out_iddfs import solve_lights_out_iddfs


def run_experiments(max_n: int = 5, timeout: float = 90.0):
    """
    Run both BFS and IDDFS on grids from 1x1 to max_n x max_n.

    Args:
        max_n: Maximum grid size to test
        timeout: Timeout in seconds for each algorithm

    Returns:
        Dictionary containing results for both algorithms
    """
    bfs_results = []
    iddfs_results = []

    print("Running experiments...")
    print("=" * 60)

    for n in range(1, max_n + 1):
        print(f"\nGrid size: {n}x{n}")

        # Run BFS
        print(f"  Running BFS...", end=" ")
        start = time.time()
        bfs_result = solve_lights_out_bfs(n, timeout=timeout)
        bfs_time = time.time() - start

        if bfs_result['timed_out']:
            print(f"TIMEOUT after {bfs_time:.2f}s")
        else:
            print(f"Done in {bfs_time:.3f}s")

        bfs_results.append({
            'n': n,
            'nodes_created': bfs_result['nodes_created'],
            'nodes_expanded': bfs_result['nodes_expanded'],
            'time': bfs_time,
            'timed_out': bfs_result['timed_out'],
            'solution_length': len(bfs_result['solution']) if bfs_result['solution'] else None
        })

        # Run IDDFS
        print(f"  Running IDDFS...", end=" ")
        start = time.time()
        iddfs_result = solve_lights_out_iddfs(n, timeout=timeout)
        iddfs_time = time.time() - start

        if iddfs_result['timed_out']:
            print(f"TIMEOUT after {iddfs_time:.2f}s")
        else:
            print(f"Done in {iddfs_time:.3f}s")

        iddfs_results.append({
            'n': n,
            'nodes_created': iddfs_result['nodes_created'],
            'nodes_expanded': iddfs_result['nodes_expanded'],
            'time': iddfs_time,
            'timed_out': iddfs_result['timed_out'],
            'solution_length': len(iddfs_result['solution']) if iddfs_result['solution'] else None
        })

    return {'bfs': bfs_results, 'iddfs': iddfs_results}


def print_comparison_table(results: dict):
    """Print a comparison table of the results."""
    bfs = results['bfs']
    iddfs = results['iddfs']

    print("\n" + "=" * 90)
    print("COMPARISON TABLE: BFS vs IDDFS")
    print("=" * 90)

    # Nodes Created comparison
    print("\nNodes Created:")
    print(f"{'N':>3} | {'BFS':>14} | {'IDDFS':>14} | {'Ratio (IDDFS/BFS)':>18}")
    print("-" * 55)
    for b, i in zip(bfs, iddfs):
        bfs_nc = b['nodes_created']
        iddfs_nc = i['nodes_created']
        ratio = iddfs_nc / bfs_nc if bfs_nc > 0 else 0
        bfs_str = f"{bfs_nc:,}" + ("*" if b['timed_out'] else "")
        iddfs_str = f"{iddfs_nc:,}" + ("*" if i['timed_out'] else "")
        print(f"{b['n']:>3} | {bfs_str:>14} | {iddfs_str:>14} | {ratio:>18.2f}")

    # Nodes Expanded comparison
    print("\nNodes Expanded:")
    print(f"{'N':>3} | {'BFS':>14} | {'IDDFS':>14} | {'Ratio (IDDFS/BFS)':>18}")
    print("-" * 55)
    for b, i in zip(bfs, iddfs):
        bfs_ne = b['nodes_expanded']
        iddfs_ne = i['nodes_expanded']
        ratio = iddfs_ne / bfs_ne if bfs_ne > 0 else 0
        bfs_str = f"{bfs_ne:,}" + ("*" if b['timed_out'] else "")
        iddfs_str = f"{iddfs_ne:,}" + ("*" if i['timed_out'] else "")
        print(f"{b['n']:>3} | {bfs_str:>14} | {iddfs_str:>14} | {ratio:>18.2f}")

    print("\n* = timed out (incomplete search)")


def create_graphs(results: dict, output_prefix: str = "lights_out"):
    """
    Create comparison graphs for nodes created and nodes expanded.

    Args:
        results: Dictionary containing BFS and IDDFS results
        output_prefix: Prefix for output file names
    """
    bfs = results['bfs']
    iddfs = results['iddfs']

    # Extract data for plotting (only non-timeout results for clean comparison)
    n_values = [r['n'] for r in bfs]
    bfs_created = [r['nodes_created'] for r in bfs]
    bfs_expanded = [r['nodes_expanded'] for r in bfs]
    iddfs_created = [r['nodes_created'] for r in iddfs]
    iddfs_expanded = [r['nodes_expanded'] for r in iddfs]

    # Graph 1: Nodes Created
    plt.figure(figsize=(10, 6))
    plt.plot(n_values, bfs_created, 'b-o', linewidth=2, markersize=8,
             label='BFS', markerfacecolor='blue')
    plt.plot(n_values, iddfs_created, 'r--s', linewidth=2, markersize=8,
             label='IDDFS', markerfacecolor='red')

    plt.xlabel('Grid Size (N)', fontsize=12)
    plt.ylabel('Nodes Created', fontsize=12)
    plt.title('Lights Out Puzzle: Nodes Created by Algorithm', fontsize=14)
    plt.legend(loc='upper left', fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.ylim(bottom=0)  # Start y-axis at 0
    plt.xticks(n_values)

    # Add value annotations
    for i, n in enumerate(n_values):
        plt.annotate(f'{bfs_created[i]:,}', (n, bfs_created[i]),
                     textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8)
        plt.annotate(f'{iddfs_created[i]:,}', (n, iddfs_created[i]),
                     textcoords="offset points", xytext=(0, -15), ha='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(f'{output_prefix}_nodes_created.png', dpi=150)
    print(f"\nSaved: {output_prefix}_nodes_created.png")
    plt.close()

    # Graph 2: Nodes Expanded
    plt.figure(figsize=(10, 6))
    plt.plot(n_values, bfs_expanded, 'b-o', linewidth=2, markersize=8,
             label='BFS', markerfacecolor='blue')
    plt.plot(n_values, iddfs_expanded, 'r--s', linewidth=2, markersize=8,
             label='IDDFS', markerfacecolor='red')

    plt.xlabel('Grid Size (N)', fontsize=12)
    plt.ylabel('Nodes Expanded', fontsize=12)
    plt.title('Lights Out Puzzle: Nodes Expanded by Algorithm', fontsize=14)
    plt.legend(loc='upper left', fontsize=11)
    plt.grid(True, alpha=0.3)
    plt.ylim(bottom=0)  # Start y-axis at 0
    plt.xticks(n_values)

    # Add value annotations
    for i, n in enumerate(n_values):
        plt.annotate(f'{bfs_expanded[i]:,}', (n, bfs_expanded[i]),
                     textcoords="offset points", xytext=(0, 10), ha='center', fontsize=8)
        plt.annotate(f'{iddfs_expanded[i]:,}', (n, iddfs_expanded[i]),
                     textcoords="offset points", xytext=(0, -15), ha='center', fontsize=8)

    plt.tight_layout()
    plt.savefig(f'{output_prefix}_nodes_expanded.png', dpi=150)
    print(f"Saved: {output_prefix}_nodes_expanded.png")
    plt.close()


### Main
if __name__ == "__main__":
    print("Lights Out Puzzle: BFS vs IDDFS Comparison")
    print("=" * 60)

    # Run experiments for grids 1x1 through 4x4
    # (5x5 times out for both algorithms)
    results = run_experiments(max_n=4, timeout=90.0)

    # Print comparison table
    print_comparison_table(results)

    # Create graphs
    create_graphs(results)

    print("\nDone! Graphs have been saved to:")
    print("  - lights_out_nodes_created.png")
    print("  - lights_out_nodes_expanded.png")
