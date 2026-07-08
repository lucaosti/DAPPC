# DAPPC - Report: LAB2, LAB3, LAB4

---

**Q1: Describe how you have obtained the clusters for each dataset (SOM victories map + dendrogram of the weight vectors + clusters)**

We trained three SOMs (10×10, 12×12, 14×14) on each of the four imputed datasets from LAB1 (knn_global, knn_by_class, clust_global, clust_by_class), for a total of 12 SOMs. Input features for each SOM are selected via a PCA-guided ranking and normalised with min-max scaling (SOM training is distance-based, so all variables must be on a comparable scale). The victories map was used to visualize how many subjects activate each neuron. Hierarchical clustering (complete linkage, cityblock distance) was then applied to the neuron weight vectors of each SOM. For each SOM, the optimal number of clusters k was selected automatically by minimizing the maximum intra-cluster variability across k = 2…25, after excluding clusters with too few assigned subjects (fewer than 1% of the dataset, minimum 3) as outliers. Contiguous regions ("bubbles") were identified using a BFS 4-connectivity algorithm to verify spatial coherence. Each subject was finally assigned to the cluster corresponding to its winning neuron.

---

**Q2: Describe how you have selected for each dataset the best set of clusters**

We compared the three SOM sizes on the knn_global dataset using the maximum intra-cluster variability (mean standard deviation per feature, maximised across clusters, computed on normalised features), excluding outlier clusters from the calculation. The 12×12 SOM gave the lowest value among the sizes actually used downstream (0.0949), indicating tight and homogeneous clusters. The 10×10 scored 0.0951 and the 14×14 scored 0.0932 (marginally lower, but 12×12 is the size used consistently downstream in LAB3/LAB4).

---

**Q3: Describe how you have selected cluster A and cluster B and the features selected for each cluster**

From the 5 clusters of the 12×12 SOM (applied to the knn_global dataset), clusters missing one of the 3 outcome classes were removed, then clusters with fewer than 100 patients were removed (this excluded a 30-patient cluster). Among the remaining clusters, the two with maximum centroid distance were selected: **Cluster 1** (n=565, Cluster A) and **Cluster 3** (n=361, Cluster B).

ACO (Setup C, iterations=150, β=3.0, λ=0.90, n_ants=10, 5-fold CV, kNN k=5) was run **independently on each cluster** (not on a shared pool later split) to identify a discriminative feature subset for each:

- **Cluster A** (id=1, n=565): 7 features — `std_temperature`, `std_platelets`, `std_wbc`, `std_diastolic_blood_pressure`, `std_respiratory_rate`, `comorb_catneurological_neuromuscular_psychiatric`, `std_phosphate`
- **Cluster B** (id=3, n=361): 10 features — `first_PT`, `first_chloride`, `first_PEEP`, `std_pH`, `std_platelets`, `std_phosphate`, `comorb_catsystemic_immune_oncologic`, `first_mean_airway_pressure`, `std_PEEP`, `sedative_duration_hours`

---

**Q4: Upload a file with the set of MF associated to each feature, the rules obtained for each cluster described using the MFs, and the results of the two FIS representing the values of the indicator**

Membership functions for every continuous feature were designed by inspecting a bar diagram (small bins) of the complete dataset and marking Low/Medium/High regions from the observed mode, spread and skew (trapezoidal at the extremes, triangular in the middle). Binary features (the two `comorb_cat*` variables) use 2 triangular MFs (peak at 0, peak at 1). The output `clinical_risk` variable uses 3 MFs over [0, 100] (Low/Medium/High); the Low/Medium and Medium/High classification thresholds (31.25 and 68.75) are the crossover points of these output MFs, not fit against the true labels.

Rules: exactly one rule per sub-cluster centroid (all selected features combined in AND), obtained via hierarchical clustering (complete linkage, cityblock) applied separately within each outcome class.

FIS results summary:
- **Cluster A** (n=565): 11 rules (one per centroid, no pairwise expansion). 426/565 subjects (75.4%) left unclassified — no fallback is applied; a subject is unclassified when no rule's AND-combined support region covers its feature values. On the 139 classified subjects: Accuracy = 48.20%, Balanced Accuracy = 49.75%.
- **Cluster B** (n=361): 8 rules. 336/361 subjects (93.1%) unclassified. On the 25 classified subjects: Accuracy = 60.00%, Balanced Accuracy = 57.58%.

Discussion (unclassified subjects): the large unclassified fraction is an expected consequence of requiring every selected feature to jointly fire in a single rule (AND of 7-10 terms) — the more features in a cluster, the smaller the joint support region of any single centroid-based rule, and the higher the fraction of subjects whose combination of values falls outside all rules' supports. Reducing this fraction would require either widening MF overlaps (more support per term) or defining more sub-cluster rules (finer dendrogram cuts) to cover more of the feature space.

Detailed MF plots and rule tables are available in `LAB4/outputs/<run>/mf_definitions_cluster1.png`, `mf_definitions_cluster4.png`, and the saved `LAB4_FIS_rules_cluster1` / `LAB4_FIS_rules_cluster4` files (the previously attached `lab4.pdf` predates this correction and should be regenerated from the current notebooks before submission).
