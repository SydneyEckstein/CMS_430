import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.mixture import GaussianMixture
from scipy.cluster.hierarchy import linkage, dendrogram

# --- Phase 1: Setup & Data Loading ---

iris = load_iris()
X = iris.data
y = iris.target
feature_names = iris.feature_names
target_names = iris.target_names

print(f"Dataset shape: {X.shape}")
print(f"Features: {feature_names}")
print(f"Classes: {target_names}")
print(f"Samples per class: {np.bincount(y)}")

# --- Phase 2: PCA Scatter Plot ---

pca = PCA(n_components=2)
X_pca = pca.fit_transform(X)

colors = ['steelblue', 'tomato', 'mediumseagreen']

plt.figure(figsize=(8, 6))
for i, species in enumerate(target_names):
    mask = y == i
    plt.scatter(X_pca[mask, 0], X_pca[mask, 1],
                color=colors[i], label=species, edgecolors='k', linewidths=0.4, s=60)

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)')
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)')
plt.title('Iris Dataset — PCA Projection (True Labels)')
plt.legend()
plt.tight_layout()
plt.savefig('pca_scatter.png', dpi=150)
plt.close()
print("Saved pca_scatter.png")
