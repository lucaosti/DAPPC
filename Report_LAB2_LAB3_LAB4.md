# DAPPC - Report: LAB2, LAB3, LAB4

---

**Q: Describe how you have obtained the clusters for each dataset (SOM victories map + dendrogram of the weight vectors + clusters)**

We trained 3 SOMs (10x10, 12x12, 14x14) on 10 clinical features. The victories map shows how many subjects activate each neuron. We then ran hierarchical clustering (complete linkage, cityblock) on the neuron weight vectors and cut the dendrogram at t=7, getting 7 clusters for each SOM. Contiguous bubbles were identified via BFS; all 7 clusters were spatially connected. Each subject was assigned to the cluster of its winning neuron.

---

**Q: Describe how you have selected for each dataset the best set of clusters**

We compared the three SOMs using the maximum intra-cluster variance (computed on normalised features). The 10x10 gave the lowest value (0.0459), meaning tighter, more homogeneous clusters, so we kept that one. The 12x12 scored 0.0461 and the 14x14 scored 0.0497.

---

**Q: Describe how you have selected cluster A and cluster B and the features selected for each cluster**

From the 7 clusters of the 10x10 SOM, we removed Cluster 6 (n=122, below the 25%-of-mean threshold of 139). Among the remaining 6, we picked the two with the most distant centroids in normalised space: Cluster 1 (n=292) and Cluster 4 (n=352), distance=1.97. ACO (Setup C) on Cluster B selected 8 features: plateau pressure, Charlson index, lactate, std MAP, std plateau pressure, and 3 binary comorbidity flags. The same set was used for both clusters.

---

**Q: Upload a file with the set of MF associated to each feature, the rules obtained for each cluster described using the MFs, and the results of the two FIS representing the values of the indicator**

See attached file: `LAB4_MF_Rules_FIS_Results.xlsx`
