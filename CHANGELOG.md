# Changelog

## 0.4.3 — 2026-11-23

- Refined the journal-cluster network: larger data nodes, more restrained on-node labels and more prominent cluster headings.
- Compressed group-level gaps in the custom cluster timeline while keeping intra-cluster term jitter.
- Rebalanced heatmap margins to prevent left-axis title/term-label overlap and retained a readable serif default.
- Updated two-panel overlay: readable labels, node-size scaling, **endpoint-to-endpoint curved edge color gradients**, and fixed **2016–2026** legend with labels every two years.
- Kept the automatically generated **600-dpi PNG, PDF and SVG** figure outputs. Font selection prefers Times New Roman, with an installed serif fallback where it is unavailable.
- Added English/Chinese README, installation, input-format, figure interpretation, methods/limitations, and contribution guidance for the public-source release.
- Existing Python test suite: 10 tests (not a substitute for real Windows GUI validation).

## 0.4.2 — 2026-11-23

- Increased keyword-label coverage and density of publication-style visualizations; subsequent v0.4.3 changes balanced label size against node size.

## 0.4.1 — 2026-11-23

- Switched defaults to 600-dpi PNG plus vector PDF/SVG and introduced a two-panel publication-year overlay.
- Enlarged chart typography and strengthened network rendering.

## 0.3.1 — 2026-11-20

- Kept the flat, clean `journal-cluster` map as the default visual style; glossy/spherical nodes are not enabled by default.
- Added a Windows file-picker launcher for selecting one or multiple bibliography exports without manually copying files into `data/raw/`.
- Added `.bat` launchers for double-click installation and analysis on Windows.
- Added an automatic keyword-frequency threshold based on approximately 2% of the corpus size (minimum 2); the chosen numeric threshold is recorded in run metadata.
- Added a Chinese user guide and GitHub publishing checklist.
- Added GitHub Actions tests for Python 3.10, 3.11, and 3.12.
- Revalidated both supplied Zotero exports: 251 records → 84 nodes / 1,146 links; 80 records → 21 nodes / 84 links.
- Automated test suite: 6 passed.

## 0.3.0

- Added Zotero CSV parser and separation of recognized organizational tags.
- Added journal-cluster visualization with curved links, dashed cluster boundaries, cluster headings, and automatic label placement.
- Added PNG/SVG/PDF exports and VOSviewer-compatible files.

## 0.4.0 — research reproducibility and Excel corpus comparison

- Read merged bibliographic `.xlsx` sheets directly without requiring desktop Excel or executing macros.
- Batch analyze overlapping five-category literature classifications from the corpus workbook.
- Preserve provenance: original bibliographic keywords vs controlled terms extracted from titles/abstracts.
- Produce per-group frequency ranks, Top-10 tables, high-frequency thresholds, cluster summaries, year-by-term tables, and longitudinal term heatmaps.
- Export a multi-group Chinese comparative report, annual group record counts, metadata coverage and classification review queue.
- Add opt-in metadata enrichment from a second bibliography export by DOI/title and optional journal-only filter.
- Do not claim CiteSpace native burst or cluster-timeline algorithms; plots are document-count heatmaps and NetworkX clusters.
