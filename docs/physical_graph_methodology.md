# Physical Graph Methodology
1.  **Extraction:** Edges are strictly drawn from chennai_highways.geojson and chennai_waterways.geojson.
2.  **Typing:** Graphs are segregated into Road and Drainage networks.
3.  **Governance:** ackend/app/core/graph_provenance.py wraps the PyTorch Geometric loaders to enforce the provenance metadata, deliberately crashing if an experiment silently merges a SYNTHETIC adjacency matrix with a REAL graph layer.
