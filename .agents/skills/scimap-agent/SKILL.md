---
name: scimap-agent
description: Run reproducible bibliometric analysis and scientific knowledge mapping from Zotero CSV, Web of Science tagged TXT, Scopus CSV, RIS exports, or a merged XLSX literature table. Use for keyword co-occurrence, thematic clusters, publication-year overlays, density maps, VOSviewer-compatible exports, and bibliometric reports. Do not use as a substitute for full-text systematic review, causal inference, or unsupported CiteSpace automation.
---

# SciMap-Agent

Use this skill to turn bibliographic exports into auditable keyword networks, visualizations, tables, and a methods-aware report.

## Workflow

1. Identify the input file(s) and database format. For `.xlsx` merged literature tables, the program supports five-category group comparisons and automatically generated Top 10 rankings / term-year heatmaps. Original author keywords and inferred title/abstract terms must never be conflated. Supported in this MVP: Zotero CSV (identified by `ZoteroKey`, `ItemType`, and `Title` headers), Web of Science tagged plain text (`.txt`, `.ciw`, `.wos`), Scopus CSV (`.csv`), and RIS (`.ris`). Do not assume a spreadsheet is a Scopus export; inspect its headers first. Zotero custom organizational tags (collection labels, P1/P2/P3, numbered topic labels, and star ratings) are separated from candidate bibliographic keywords and retained in `zotero_tags`. Review this extraction before interpreting the network.
2. Preserve the original files. Never overwrite or modify files in `data/raw/`.
3. Ask for clarification only if the requested analysis cannot be inferred. Otherwise use the documented defaults and report them.
4. Check duplicate records, missing years, missing keywords, and likely mixed database exports. If multiple databases are combined, disclose that source-specific field coverage may differ.
5. Review `config/thesaurus.csv` before merging synonyms. Do not merge terms merely because they look similar; keep a copy of the mapping in the project outputs.
6. Run the analysis from the repository root. On Windows, users may alternatively double-click or run `run_analysis_windows.ps1` to select bibliography files in a file dialog:

   ```bash
   python -m pip install -r requirements.txt
   python -m pip install -e .
   scimap analyze --input data/raw --output outputs --min-occurrences auto
   ```

   If the `scimap` command is unavailable, use `python -m scimap_agent.cli` after installing the package.
7. Use the built-in `journal-cluster` visualization style by default. It automatically applies a compact ForceAtlas2 layout (spring-layout fallback), curved translucent links, cluster-colored nodes, dashed cluster boundaries, data-derived cluster headings, importance-ranked labels, and automatic label-collision relaxation. Keep this flat, clean style as the default; do not switch to glossy/spherical nodes unless the user explicitly requests that alternative. Do not ask users to manually tune ordinary figure styling.
8. Inspect the generated report and figures. Verify that labels, clusters, thresholds, and publication-year ranges make sense. Cluster headings are generated from each cluster's highest-frequency non-overlapping terms; they are descriptive aids, not independently validated semantic classifications.
9. Deliver the generated report, figures, tables, and VOSviewer exports. Explain that the MVP uses NetworkX greedy modularity for community detection and ForceAtlas2 for layout; it does not claim to reproduce CiteSpace or VOSviewer's proprietary algorithms.

## Outputs

- `outputs/figures/keyword_network.png`: publication-style cluster map with curved links, dashed hulls, topic headings, and automatic label placement.
- `outputs/figures/visual_style.json`: visualization style and layout metadata.
- `outputs/figures/keyword_overlay.png`: average-publication-year overlay.
- `outputs/figures/keyword_density.png`: smoothed density surface over the network layout.
- `outputs/tables/keyword_nodes.csv` and `keyword_edges.csv`: network data.
- `outputs/tables/normalized_records.csv` and `record_keywords.csv`: cleaned records and extracted terms.
- `outputs/vosviewer/vosviewer_map.txt`, `vosviewer_network.txt`, and `vosviewer_network.json`: VOSviewer-compatible network exports.
- `outputs/reports/analysis_report.md`: quantitative summary and method notes.

## Interpretation safeguards

- Keyword co-occurrence indicates terms appearing in the same record; it does not establish causality.
- Cluster detection is algorithm-dependent. Report the algorithm and parameters.
- The MVP's NetworkX ForceAtlas2 layout (spring-layout fallback) is not the VOSviewer layout algorithm.
- A keyword's average publication year is computed from records containing that keyword.
- Bibliometric maps are descriptive evidence. Use full-text reading and domain expertise to interpret research gaps and mechanisms.
- Do not claim CiteSpace burst detection, co-citation analysis, or timeline functionality unless a validated adapter and required cited-reference data are available. Zotero CSV exports without cited-reference lists cannot support co-citation or bibliographic-coupling networks.

## Comparative Excel corpus mode (v0.4.0)

```bash
scimap analyze --input "data/raw/merged_corpus.xlsx" --output outputs/comparison --min-occurrences 5
# If a richer export with abstracts and keywords exists:
scimap analyze --input "data/raw/merged_corpus.xlsx" --enrich-with "data/raw/full_metadata.csv" --output outputs/enriched
# For journals only:
scimap analyze --input "data/raw/merged_corpus.xlsx" --publication-type journal --output outputs/journals
```

The Excel importer uses a read-only XML workbook reader. For tables with categories `Total literature`, `Carbon emissions`, `Refinery carbon emissions`, `ML + carbon emissions`, `ML + refinery carbon emissions`, it automatically creates individual group folders and a `comparison/` summary. Groups are overlapping filters and should NOT be summed. Without author keywords or abstracts, `--term-source auto` uses controlled title terms from `config/title_term_patterns.csv`; this is not true author-keyword co-occurrence. Counts are documents containing each term, not raw string occurrences. For groups <50 records, display a sensitivity/exploratory map with threshold 2 while maintaining threshold 5 for larger groups; clearly label this distinction.

Images: `keyword_network.png`, `keyword_overlay.png`, `keyword_density.png`, `keyword_timeline.png`, `cluster_timeline.png` and SVG (the timeline is a **year-by-term heatmap**, not CiteSpace burst or cluster timeline). Tables: `keyword_frequency_all.csv`, `high_frequency_keywords.csv`, `top10_keywords.csv`, `keyword_year_counts.csv`, `cluster_summary.csv`; high-level `comparison/top10_comparison_long.csv` and `comparison/group_year_counts.csv` and screening `classification_review_queue.csv`. Review formula-based category labels with abstracts/full text before publishing.

## Current release (v0.4.3)

Use 600 dpi for PNG and always provide SVG and PDF where the plot supports it. For comparative XLSX mode, the project also produces group-specific Top-10 tables, a cluster timeline, a term-year heatmap, and a two-panel overlay with 2016–2026 legend and endpoint-gradient edges. Treat those temporal figures as SciMap-Agent custom products, never as CiteSpace native output. The original bibliographic keyword source must be clearly distinguished from inferred controlled terms. Exact Times New Roman typography depends on a local font installation.
