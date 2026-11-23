# Analysis methods and definitions

- **Keyword occurrence**: number of distinct records containing a normalized keyword.
- **Keyword co-occurrence**: number of records containing both keywords. Each keyword is counted once per record.
- **Total link strength**: sum of co-occurrence weights on all links connected to a keyword.
- **Cluster**: community detected by NetworkX greedy modularity using co-occurrence weights.
- **Average publication year**: arithmetic mean of publication years for records containing the keyword.
- **Overlay visualization**: node color encodes average publication year.
- **Density visualization**: Gaussian-smoothed weighted histogram over the ForceAtlas2 (or spring-layout fallback) coordinates. It is not a native VOSviewer density map.

The network uses a document-level binary co-occurrence model. It does not currently implement fractional counting, association-strength normalization, bibliographic coupling, co-citation analysis, or burst detection.
