# Phased Implementation Plan: Clustering Analysis on Fisher's Iris Dataset

---

## Phase 1 — Setup & Data Loading
**Goal:** Load the iris dataset and establish the project structure.

- Import required libraries: `sklearn`, `matplotlib`, `numpy`, `scipy`
- Load iris dataset via `sklearn.datasets.load_iris()`
- Create a single `clustering.py` file (or notebook) to house all phases
- Verify data shape: 150 samples x 4 features, 3 class labels

---

## Phase 2 — PCA Scatter Plot (2 Most Important Dimensions)
**Goal:** Project 4D data into 2D using PCA and visualize class separation.

- Apply `sklearn.decomposition.PCA(n_components=2)` to reduce to 2D
- Plot scatter colored by true species labels
- Annotate which component is PC1/PC2
- Observe: setosa should be clearly separated; versicolor/virginica overlap
- Save as `pca_scatter.png`

---

## Phase 3 — K-Means Clustering (k=3)
**Goal:** Run k-means and overlay cluster assignments on the PCA scatter plot.

- Fit `sklearn.cluster.KMeans(n_clusters=3)` on the full 4-feature data
- Plot PCA projection again, colored by **cluster assignment** (not true labels)
- Mark centroids projected into PCA space
- Compare visually to true labels from Phase 2
- Save as `kmeans_pca.png`

---

## Phase 4 — Petal-Only Scatter Plot
**Goal:** Determine if petal width & length alone can separate one class.

- Plot `petal_length` vs `petal_width` colored by true species
- Observe: setosa is cleanly separable; versicolor/virginica overlap
- Save as `petal_scatter.png`
- Answer the question: *yes, setosa is separable by petal measurements alone*

---

## Phase 5 — Silhouette Plot (k = 2 to 10)
**Goal:** Identify the optimal number of clusters using silhouette scores.

- Loop k from 2 to 10, fit KMeans, compute `sklearn.metrics.silhouette_score`
- Plot 1 — average silhouette score vs k (line chart): identifies best k at a glance. Save as `silhouette_plot.png`
- Plot 2 — per-point silhouette plot grid (3x3): shows individual point scores grouped by cluster for every k using `silhouette_samples`. Red dashed line marks the cluster average. Save as `silhouette_detail.png`
- Best k = 2 (score: 0.681), suggesting versicolor/virginica are not well-separated as distinct clusters

---

## Phase 6 — Hierarchical Clustering Dendrogram
**Goal:** Build and visualize a Ward's linkage dendrogram.

- Use `scipy.cluster.hierarchy.linkage(data, method='ward')`
- Plot with `scipy.cluster.hierarchy.dendrogram()` — full dendrogram showing all 150 leaves (no truncation)
- Color threshold computed dynamically as midpoint between 2nd and 3rd top-level merge distances to reliably highlight exactly 3 clusters
- Dashed horizontal line marks the cut point
- Save as `dendrogram.png`
- Observe how the merge sequence reflects setosa separating early, versicolor/virginica merging late

---

## Phase 7 — Gaussian Mixture Model (GMM)
**Goal:** Apply a probabilistic clustering and compare to true labels.

- Fit `sklearn.mixture.GaussianMixture(n_components=3)`
- Predict cluster assignments and plot on PCA scatter
- Compare GMM assignments to true species and to k-means assignments
- Note: GMM can model elliptical clusters (unlike k-means' spherical assumption), potentially better separating versicolor/virginica
- Save as `gmm_scatter.png`

---

## Phase 8 — Submission Packaging
**Goal:** Collect all outputs for submission.

Plots to submit:

| File | Phase |
|---|---|
| `pca_scatter.png` | 2 |
| `kmeans_pca.png` | 3 |
| `petal_scatter.png` | 4 |
| `silhouette_plot.png` | 5 |
| `silhouette_detail.png` | 5 |
| `dendrogram.png` | 6 |
| `gmm_scatter.png` | 7 |

- Clean up code, add comments explaining key decisions
- Submit `clustering.py` + all `.png` files

---

## Key Libraries Summary

```
sklearn  — KMeans, PCA, GaussianMixture, silhouette_score, load_iris
scipy    — linkage, dendrogram (hierarchical clustering)
matplotlib — all plotting
numpy    — array operations
```
