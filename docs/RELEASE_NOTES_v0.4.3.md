# SciMap-Agent v0.4.3 — Public beta

**Release date:** 2026-11-23

SciMap-Agent is a local Python utility and optional Codex Agent Skill for bibliographic metadata analysis, document-level term co-occurrence mapping, temporal graphics and editable figure export.

## Highlights

- Zotero CSV, Web of Science tagged TXT/CIW/WOS, Scopus CSV, RIS, and recognized five-group XLSX literature workbook import.
- Auditable full-counting term frequency statistics, Top 10 tables and network clustering.
- Journal-oriented visuals: cluster networks, publication-year overlays, density maps, custom cluster timeline, annual term heatmap and (for grouped workbooks) an A/B overlay.
- **600 dpi PNG** alongside **PDF/SVG** figure exports; Times New Roman preferred when installed, with serif fallback.
- Cluster figures updated with clearer nodes, term labels and group headings; custom timeline spacing adjusted; heatmap axis spacing improved.
- Two-panel overlay uses **2016–2026** time colorbar at two-year intervals and **curved endpoint-color gradient links**.
- Chinese and English README, installation guide, data format specifications, figure explanation, scientific method limitations and contributor instructions.

## Verification

- Automated Python tests: **10 passed** in the development runtime.
- Synthetic WoS smoke test: **6 mock records**, generating 8 nodes and 24 edges with PNG/PDF/SVG output.
- Windows GUI launch flow has **not** been separately verified on a Windows computer; it is implemented via PowerShell file dialogs, not a compiled executable.

## Scientific limitations

The cluster time-series graphics are **SciMap-Agent custom visualizations**, not native CiteSpace time-zone/timeline or burst outputs. No official CiteSpace MCP interface, co-citation, bibliographic-coupling implementation, or fully automated systematic-review screening is claimed. Inferred title/abstract vocabulary must not be presented as original author keywords. Bibliographic group flags can contain misclassifications; manuscript authors must review inclusion decisions and dense chart labels.

## Safety and source distribution

The public-source ZIP contains **only code, docs and synthetic samples**. No personal Zotero CSVs, 936-record master workbook, unpublished manuscript, PDF corpus or study-specific results are included.

License: MIT (`LICENSE`).
