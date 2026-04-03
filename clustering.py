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

# --- Phase 3: K-Means Clustering (k=3) ---

kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
kmeans.fit(X)
km_labels = kmeans.labels_

# Project centroids into PCA space
centroids_pca = pca.transform(kmeans.cluster_centers_)

plt.figure(figsize=(8, 6))
for i in range(3):
    mask = km_labels == i
    plt.scatter(X_pca[mask, 0], X_pca[mask, 1],
                color=colors[i], label=f'Cluster {i}', edgecolors='k', linewidths=0.4, s=60)

plt.scatter(centroids_pca[:, 0], centroids_pca[:, 1],
            color='black', marker='X', s=180, zorder=5, label='Centroids')

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)')
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)')
plt.title('Iris Dataset — K-Means Clustering (k=3)')
plt.legend()
plt.tight_layout()
plt.savefig('kmeans_pca.png', dpi=150)
plt.close()
print("Saved kmeans_pca.png")
