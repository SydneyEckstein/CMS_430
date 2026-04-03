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

# --- Phase 4: Petal-Only Scatter Plot ---

# petal length = index 2, petal width = index 3
plt.figure(figsize=(8, 6))
for i, species in enumerate(target_names):
    mask = y == i
    plt.scatter(X[mask, 2], X[mask, 3],
                color=colors[i], label=species, edgecolors='k', linewidths=0.4, s=60)

plt.xlabel('Petal Length (cm)')
plt.ylabel('Petal Width (cm)')
plt.title('Iris Dataset — Petal Length vs. Petal Width (True Labels)')
plt.legend()
plt.tight_layout()
plt.savefig('petal_scatter.png', dpi=150)
plt.close()
print("Saved petal_scatter.png")

# --- Phase 5: Silhouette Plot (k=2 to 10) ---

k_values = range(2, 11)
silhouette_scores = []

for k in k_values:
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    score = silhouette_score(X, labels)
    silhouette_scores.append(score)
    print(f"  k={k}: silhouette score = {score:.4f}")

best_k = k_values[silhouette_scores.index(max(silhouette_scores))]
print(f"Best k by silhouette score: {best_k}")

plt.figure(figsize=(8, 5))
plt.plot(list(k_values), silhouette_scores, marker='o', color='steelblue', linewidth=2)
plt.axvline(x=best_k, color='tomato', linestyle='--', label=f'Best k={best_k}')
plt.xlabel('Number of Clusters (k)')
plt.ylabel('Average Silhouette Score')
plt.title('Silhouette Scores for k=2 to 10 (Iris Dataset)')
plt.xticks(list(k_values))
plt.legend()
plt.tight_layout()
plt.savefig('silhouette_plot.png', dpi=150)
plt.close()
print("Saved silhouette_plot.png")

# Per-point silhouette plots for k=2 to 10
from sklearn.metrics import silhouette_samples

fig, axes = plt.subplots(3, 3, figsize=(15, 12))
axes = axes.flatten()

for idx, k in enumerate(k_values):
    km = KMeans(n_clusters=k, random_state=42, n_init=10)
    labels = km.fit_predict(X)
    sample_scores = silhouette_samples(X, labels)
    avg_score = silhouette_scores[idx]

    ax = axes[idx]
    y_lower = 10
    for cluster in range(k):
        cluster_scores = np.sort(sample_scores[labels == cluster])
        size = cluster_scores.shape[0]
        y_upper = y_lower + size
        ax.barh(range(y_lower, y_upper), cluster_scores, height=1.0, edgecolor='none')
        y_lower = y_upper + 10

    ax.axvline(x=avg_score, color='red', linestyle='--', linewidth=1)
    ax.set_title(f'k={k} (avg={avg_score:.3f})')
    ax.set_xlabel('Silhouette Score')
    ax.set_ylabel('Cluster')
    ax.set_yticks([])
    ax.set_xlim([-0.2, 1.0])

plt.suptitle('Per-Point Silhouette Plots for k=2 to 10 (Iris Dataset)', fontsize=14)
plt.tight_layout()
plt.savefig('silhouette_detail.png', dpi=150)
plt.close()
print("Saved silhouette_detail.png")

# --- Phase 6: Hierarchical Clustering Dendrogram ---

linked = linkage(X, method='ward')

# Dynamically set color threshold to highlight exactly 3 clusters:
# cut between the 3rd-to-last and 2nd-to-last merge distances
color_threshold = (linked[-3, 2] + linked[-2, 2]) / 2

plt.figure(figsize=(18, 6))
dendrogram(linked,
           color_threshold=color_threshold,
           above_threshold_color='gray',
           leaf_rotation=90,
           leaf_font_size=6)

plt.axhline(y=color_threshold, color='black', linestyle='--', linewidth=0.8, label=f'Cut (3 clusters)')
plt.xlabel('Sample Index')
plt.ylabel('Ward Distance')
plt.title('Hierarchical Clustering Dendrogram — Ward\'s Linkage (Iris Dataset)')
plt.legend()
plt.tight_layout()
plt.savefig('dendrogram.png', dpi=150)
plt.close()
print("Saved dendrogram.png")

# --- Phase 7: Gaussian Mixture Model ---

gmm = GaussianMixture(n_components=3, random_state=42)
gmm.fit(X)
gmm_labels = gmm.predict(X)

plt.figure(figsize=(8, 6))
for i in range(3):
    mask = gmm_labels == i
    plt.scatter(X_pca[mask, 0], X_pca[mask, 1],
                color=colors[i], label=f'GMM Cluster {i}', edgecolors='k', linewidths=0.4, s=60)

plt.xlabel(f'PC1 ({pca.explained_variance_ratio_[0]*100:.1f}% variance)')
plt.ylabel(f'PC2 ({pca.explained_variance_ratio_[1]*100:.1f}% variance)')
plt.title('Iris Dataset — Gaussian Mixture Model Clustering (k=3)')
plt.legend()
plt.tight_layout()
plt.savefig('gmm_scatter.png', dpi=150)
plt.close()
print("Saved gmm_scatter.png")

# Compare GMM assignments to true labels
from sklearn.metrics import accuracy_score
from itertools import permutations

# Find best label mapping (since cluster IDs are arbitrary)
best_acc = 0
for perm in permutations([0, 1, 2]):
    mapped = np.array([perm[l] for l in gmm_labels])
    acc = accuracy_score(y, mapped)
    if acc > best_acc:
        best_acc = acc

print(f"GMM clustering accuracy (best label mapping): {best_acc*100:.1f}%")

# Compare k-means for reference
best_acc_km = 0
for perm in permutations([0, 1, 2]):
    mapped = np.array([perm[l] for l in km_labels])
    acc = accuracy_score(y, mapped)
    if acc > best_acc_km:
        best_acc_km = acc

print(f"K-Means clustering accuracy (best label mapping): {best_acc_km*100:.1f}%")
