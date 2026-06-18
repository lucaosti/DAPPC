# DAPPC - Report: LAB2, LAB3, LAB4

---

**Q1: Describe how you have obtained the clusters for each dataset (SOM victories map + dendrogram of the weight vectors + clusters)**

We trained three SOMs (10×10, 12×12, 14×14) on each of the four imputed datasets from LAB1 (knn_global, knn_by_class, clust_global, clust_by_class), for a total of 12 SOMs. The victories map was used to visualize how many subjects activate each neuron. Hierarchical clustering (complete linkage, cityblock distance) was then applied to the neuron weight vectors of each SOM. For each SOM, the optimal number of clusters k was selected automatically by minimizing the maximum intra-cluster variability across k = 2…25. Contiguous regions ("bubbles") were identified using a BFS 4-connectivity algorithm to verify spatial coherence. Each subject was finally assigned to the cluster corresponding to its winning neuron.

---

**Q2: Describe how you have selected for each dataset the best set of clusters**

We compared the three SOM sizes on the knn_global dataset using the maximum intra-cluster variability (mean standard deviation per feature, maximised across clusters, computed on normalised features). The 12×12 SOM gave the lowest value (1.0013), indicating the tightest and most homogeneous clusters, and was therefore selected. The 10×10 scored 1.0195 and the 14×14 scored 1.0185.

---

**Q3: Describe how you have selected cluster A and cluster B and the features selected for each cluster**

From the 22 clusters of the 12×12 SOM (applied to the knn_global dataset), all 22 clusters contained all three outcome classes. Clusters with fewer than 44 subjects (25% of the mean cluster size of 177.0) were discarded, leaving 15 valid clusters. Among these, the two with the most distant centroids in normalised feature space were Cluster 13 (n=290, Cluster A) and Cluster 14 (n=79, Cluster B), with a centroid distance of 1.9966.

ACO (Setup C, iterations=150, β=3.0, λ=0.90, n_ants=10, 5-fold CV) was run on Cluster B and selected 5 features: `age`, `std_platelets`, `comorb_catsystemic_immune_oncologic`, `first_PT`, `std_heart_rate` (best CV balanced accuracy = 0.6623, objective = 0.3112). The full tabular detail of the selected features — including domain, type, unit and description — is reported in the attached file: `lab3_features.pdf`.

---

**Q4: Upload a file with the set of MF associated to each feature, the rules obtained for each cluster described using the MFs, and the results of the two FIS representing the values of the indicator**

See attached file: `LAB4_FIS_MF_Rules.pdf`

FIS results summary:
- **Cluster A** (n=28): 83 unique fuzzy rules (7 centroid-based + pairwise expansions). Overall Accuracy = 25.00%, Balanced Accuracy = 50.00%. Thresholds: Low/Medium = 15, Medium/High = 50. All 28 subjects classified by FIS (0 fallbacks).
- **Cluster B** (n=51): 54 unique fuzzy rules (8 centroid-based + pairwise expansions). Overall Accuracy = 64.71%, Balanced Accuracy = 39.70%. Thresholds: Low/Medium = 55, Medium/High = 65. All 51 subjects classified by FIS (0 fallbacks).
