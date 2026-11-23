# SciMap-Agent default visual style specification

The default network figure is `journal-cluster` (v0.4.3), inspired by the supplied reference map. The goal is to produce a polished first-pass research figure automatically while preserving the underlying bibliometric network. The goal is to reduce manual styling, but dense networks still require inspection for overlapping labels at journal column width.

## Visual system

| Element | Default treatment | Data meaning |
|---|---|---|
| Canvas | White, landscape-oriented network plot | Presentation surface only |
| Cluster colors | Muted coral, blue, green, ochre, purple, then extended palette | Community membership detected by weighted greedy modularity |
| Nodes | Semi-transparent filled circles with white outlines | Size scales with number of records containing the keyword |
| Edges | Curved, translucent quadratic Bezier links | Width scales with document-level co-occurrence count |
| Within-cluster edges | Inherit cluster color | Co-occurrence between terms assigned to the same community |
| Cross-cluster edges | Muted blended tint | Co-occurrence across detected communities |
| Cluster boundaries | Soft ellipses with dark dashed outlines and faint color fills | Visual grouping only; does not change community membership |
| Cluster headings | Bold colored `#` heading built from the two most frequent non-overlapping terms | Data-derived descriptive label, not an AI-validated topic classification |
| Keyword labels | Importance-ranked, automatically collision-relaxed | Selected labels only; all nodes remain in the exported node table |

## Automatic layout and label handling

1. Use NetworkX ForceAtlas2 when available; fall back to NetworkX spring layout if not.
2. If the graph contains disconnected components, lay out each component and pack smaller components near the main component so they do not drift to distant corners.
3. Preserve the observed nodes, edges, weights, and detected cluster assignments. Visual packing does not add synthetic edges.
4. Select labels by document frequency and weighted degree. Always retain labels for very small clusters so a small component remains interpretable.
5. Resolve text-label collisions in display coordinates. If a label must move substantially, draw a subtle leader line to its node.
6. Export PNG, SVG, and PDF together; keep vector text editable when the installed font supports it.

## v0.4.3 display details

- 600-dpi PNG plus SVG and PDF by default. English text prefers Times New Roman when installed, with a serif fallback otherwise.
- Network labels and node sizes were rebalanced; keyword labels are rendered without opaque white boxes. The data-derived cluster headings are prominent.
- The comparative two-panel overlay has 2016–2026 ticks every two years. Its curved links blend the colors of the endpoint nodes; this display gradient does not encode an additional measured variable.
- The custom cluster timeline uses reduced inter-group whitespace. The yearly heatmap separates the left y-axis title from the term labels.

## Reproducibility

The run metadata records the occurrence threshold, keyword cap, community detection method, layout method, counting method, and resolution. The figure directory contains `visual_style.json` describing the renderer settings. Cluster headings and boundaries are presentation aids; they must not be treated as evidence independent of the network data.
