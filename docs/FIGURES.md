# Output figure and file reference / 图表解释

## Common figures (one ordinary export)

| File stem | Interpretation | What not to claim |
|---|---|---|
| `keyword_network` | Keyword/co-term network. Node size encodes document frequency; color encodes detected community; curved lines encode weighted co-occurrence. | Do not interpret positions/ellipse outlines as calibrated spatial distances or causal links. |
| `keyword_overlay` | Same type of network with node color representing average associated publication year. | Node color is **not** the earliest publication year, a trend test or a burst score. |
| `keyword_density` | Smoothed display-space density of keyword nodes weighted by occurrence count. | This is not a geographic density surface. |
| `keyword_timeline` | Term-by-year heatmap of document counts. | It is not CiteSpace native timeline or burst detection. |
| `cluster_timeline` | Custom cluster-grouped annual representative-term bubble/line chart. | It is not CiteSpace's clustering algorithm or native time-zone layout. |

The first three network-derived figures are created by `visualize.py`. For recognized five-group XLSX comparative mode, the temporal charts above are generated for each group by `extended_analysis.py`. In ordinary single-file mode, `keyword_timeline` is generated; `cluster_timeline` is currently a comparative-group feature.

### Two-panel overlay

For a recognized grouped XLSX workbook, `comparison/two_panel_keyword_overlay` compares two automatically selected thematic groups (currently refinery carbon emissions and ML + carbon emissions when available). Colorbar labels are fixed at **2016, 2018, 2020, 2022, 2024, 2026**. Each curved connection transitions from its first endpoint's color to its second endpoint's color. Colors show the **average associated publication year** clipped to the legend range, not direction or thematic influence.

## Export formats

For supported plotted figures, the program writes **PNG at 600 dpi**, plus **PDF** and **SVG** vector formats. The PNG's pixel dimensions vary with each figure's physical dimensions and automatic cropping. Fonts are editable text in SVG/PDF where supported by the rendering device; exact text appearance depends on locally available fonts. A publication's figure size, file rules and minimum readable font remain the author's responsibility.

## Data and report artifacts

| Output | Contents |
|---|---|
| `tables/keyword_nodes.csv` | Node attributes, occurrence, cluster and centrality/link indicators |
| `tables/keyword_edges.csv` | Co-occurring term pairs and weights |
| `tables/keyword_frequency_all.csv`, `high_frequency_keywords.csv` | Document-level term frequencies |
| `tables/top10_keywords.csv` | Ten highest-frequency terms at the selected threshold |
| `tables/keyword_year_counts.csv` | Observed document count for each term–year pair |
| `tables/cluster_summary.csv` | Cluster sizes and representative terms (group mode) |
| `comparison/group_summary.csv` | Counts and parameters for recognized overlapping XLSX groups |
| `comparison/top10_comparison_long.csv` | All group Top 10 lists in long format |
| `comparison/classification_review_queue.csv` | Items flagged for **human review**, not automatically classified as false positives |
| `reports/analysis_report.md` | Run-specific network summary, settings and limitations |
| `vosviewer/vosviewer_map.txt`, `vosviewer_network.txt`, `vosviewer_network.json` | Interoperable exports intended for downstream VOSviewer import where supported |

Some outputs are conditional on input mode, so a single-file import will not produce all `comparison/` files. The cross-software export is **file compatibility**, not an official CiteSpace/VOSviewer MCP integration.

## Interpreting visually crowded maps

Do not increase all labels indefinitely: if text overlaps nodes or cluster boundaries, a figure may be unfit for direct journal submission even at 600 dpi. Use the SVG/PDF to inspect at target journal column width and document any substantive pruning or threshold adjustment. Automated readability is a best-effort layout process.
