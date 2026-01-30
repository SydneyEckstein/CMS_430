"""
N-Queens: BFS vs IDS Performance Comparison Graphs

DSM and Claude, 2026
"""

import matplotlib.pyplot as plt

# Data from experiments
n_values = list(range(1, 10))

# BFS results
bfs_created = [2, 3, 6, 17, 54, 153, 552, 2057, 8394]
bfs_expanded = [2, 3, 6, 16, 45, 150, 513, 1966, 8043]

# IDS results
ids_created = [3, 7, 17, 41, 107, 388, 1355, 5622, 24053]
ids_expanded = [2, 4, 11, 26, 63, 239, 843, 3657, 16011]

# Create figure with two subplots side by side
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

# Graph 1: Nodes Created
ax1.plot(n_values, bfs_created, 'o-', color='blue', linewidth=2,
         markersize=8, label='BFS')
ax1.plot(n_values, ids_created, 's--', color='red', linewidth=2,
         markersize=8, label='IDS')
ax1.set_xlabel('Board Size (n)', fontsize=12)
ax1.set_ylabel('Nodes Created', fontsize=12)
ax1.set_title('N-Queens: Nodes Created Comparison', fontsize=14)
ax1.set_ylim(bottom=0)
ax1.set_xticks(n_values)
ax1.legend(loc='upper left', fontsize=11)
ax1.grid(True, alpha=0.3)

# Graph 2: Nodes Expanded
ax2.plot(n_values, bfs_expanded, 'o-', color='blue', linewidth=2,
         markersize=8, label='BFS')
ax2.plot(n_values, ids_expanded, 's--', color='red', linewidth=2,
         markersize=8, label='IDS')
ax2.set_xlabel('Board Size (n)', fontsize=12)
ax2.set_ylabel('Nodes Expanded', fontsize=12)
ax2.set_title('N-Queens: Nodes Expanded Comparison', fontsize=14)
ax2.set_ylim(bottom=0)
ax2.set_xticks(n_values)
ax2.legend(loc='upper left', fontsize=11)
ax2.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('n_queens_comparison.png', dpi=150, bbox_inches='tight')
plt.show()

print("Graph saved to n_queens_comparison.png")
