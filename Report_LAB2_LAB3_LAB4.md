# DAPPC - Report: LAB2, LAB3, LAB4

---

**Q1: Describe how you have obtained the clusters for each dataset (SOM victories map + dendrogram of the weight vectors + clusters)**

We trained three SOMs (10×10, 12×12, and 14×14). The victories map was used to visualize how many subjects activate each neuron. We then applied hierarchical clustering (complete linkage, cityblock distance) to the neuron weight vectors. The dendrogram was cut at t=7, a value selected after multiple experiments as it provided the most stable and interpretable clustering solution. This resulted in 7 clusters for each SOM. Contiguous regions (“bubbles”) were identified using a BFS algorithm, confirming that all clusters were spatially connected. Finally, each subject was assigned to the cluster corresponding to its winning neuron.

---

**Q2: Describe how you have selected for each dataset the best set of clusters**

We compared the three SOMs using the maximum intra-cluster variance (computed on normalised features). The 10x10 gave the lowest value (0.0459), meaning tighter, more homogeneous clusters, so we kept that one. The 12x12 scored 0.0461 and the 14x14 scored 0.0497.

---

**Q3: Describe how you have selected cluster A and cluster B and the features selected for each cluster**

From the 7 clusters of the 10x10 SOM, we removed Cluster 6 (n=122, below the 25%-of-mean threshold of 139). Among the remaining 6, we picked the two with the most distant centroids in normalised space: Cluster 1 (n=292) and Cluster 4 (n=352), distance=1.97. ACO (Setup C) on Cluster B selected 8 features: plateau pressure, Charlson index, lactate, std MAP, std plateau pressure, and 3 binary comorbidity flags. The same set was used for both clusters.

---

**Q4: Upload a file with the set of MF associated to each feature, the rules obtained for each cluster described using the MFs, and the results of the two FIS representing the values of the indicator**

See attached file: `LAB4_MF_Rules_FIS_Results.xlsx`
