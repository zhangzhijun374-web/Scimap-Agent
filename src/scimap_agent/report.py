from __future__ import annotations

from pathlib import Path

import pandas as pd


def write_report(records: pd.DataFrame, nodes: pd.DataFrame, edges: pd.DataFrame,
                 output_path: str | Path, input_files: list[str] | None = None,
                 parameters: dict | None = None) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    years = records["year_num"].dropna() if "year_num" in records else pd.Series(dtype=float)
    clusters = nodes.groupby("cluster").size().sort_values(ascending=False) if not nodes.empty else pd.Series(dtype=int)
    top_terms = nodes.head(15) if not nodes.empty else nodes
    top_edges = edges.head(15) if not edges.empty else edges
    parameters = parameters or {}

    lines = [
        "# SciMap-Agent Bibliometric Analysis Report", "",
        "> This report is a quantitative screening output. Cluster labels and substantive interpretations require researcher review.", "",
        "## 1. Dataset overview", "",
        f"- Records after deduplication: **{len(records)}**",
        f"- Duplicate records removed: **{records.attrs.get('duplicates_removed', 0)}**",
        f"- Records with at least one extracted keyword: **{int(records['keywords'].map(bool).sum()) if 'keywords' in records else 0}**",
        f"- Publication year range: **{int(years.min()) if len(years) else 'NA'}–{int(years.max()) if len(years) else 'NA'}**",
        f"- Keywords in network: **{len(nodes)}**",
        f"- Co-occurrence links: **{len(edges)}**",
        f"- Minimum keyword occurrence threshold: **{parameters.get('min_occurrences', 'not recorded')}**",
        f"- Maximum network keywords: **{parameters.get('max_keywords', 'not recorded')}**",
        f"- Displayed labels: **{parameters.get('max_labels') if parameters.get('max_labels') else 'automatic, importance-ranked'}**",
        f"- Visualization style: **{parameters.get('visualization_style', 'journal-cluster')}**",
        f"- Figure resolution: **{parameters.get('dpi', 'not recorded')} dpi**",
        "",
        "### Input files", "",
    ]
    for f in (input_files or []):
        lines.append(f"- `{f}`")
    lines += ["", "## 2. Most frequent keywords", "", "| Keyword | Documents | Links | Total link strength | Cluster |", "|---|---:|---:|---:|---:|"]
    for _, row in top_terms.iterrows():
        lines.append(f"| {row['keyword']} | {int(row['occurrences'])} | {int(row['links'])} | {int(row['total_link_strength'])} | {int(row['cluster'])} |")
    lines += ["", "## 3. Strongest keyword co-occurrences", "", "| Keyword A | Keyword B | Co-occurrence count |", "|---|---|---:|"]
    for _, row in top_edges.iterrows():
        lines.append(f"| {row['source']} | {row['target']} | {int(row['weight'])} |")
    lines += ["", "## 4. Cluster size summary", ""]
    if len(clusters):
        for cluster_id, size in clusters.items():
            members = nodes.loc[nodes["cluster"] == cluster_id].sort_values("occurrences", ascending=False)["keyword"].head(8).tolist()
            lines.append(f"- Cluster {cluster_id}: {int(size)} keywords. Frequent terms: {', '.join(members)}")
    else:
        lines.append("- No clusters were generated under the selected threshold.")
    lines += [
        "", "## 5. Output files", "",
        "- `figures/keyword_network.png`: publication-style cluster map with curved links, dashed hulls, topic headings, and automatic label placement.",
        "- `figures/visual_style.json`: recorded visualization style settings.",
        "- `figures/keyword_overlay.png`: average publication-year overlay network.",
        "- `figures/keyword_density.png`: density surface based on the network layout.",
        "- `tables/keyword_nodes.csv` and `tables/keyword_edges.csv`: network data.",
        "- `vosviewer/vosviewer_map.txt`, `vosviewer_network.txt`, `vosviewer_network.json`: VOSviewer-compatible exports.",
        "", "## 6. Methods and cautions", "",
        "- Keyword frequency is counted at the document level; repeated occurrences within one record count once.",
        "- Co-occurrence is counted when two normalized keywords appear in the same record.",
        "- Communities are detected using NetworkX greedy modularity with edge weights (full counting).",
        "- The plotted coordinates use ForceAtlas2 (with a NetworkX spring-layout fallback), not the proprietary VOSviewer layout algorithm.",
        "- The publication-style map uses curved co-occurrence links, cluster-colored nodes, dashed cluster hulls, data-derived cluster headings, and automatic label-collision relaxation.",
        "- Cluster headings are generated from the most frequent non-overlapping terms in each detected cluster; they are descriptive labels, not independently validated semantic classifications.",
        "- The density image is a smoothed density surface of keyword positions, not a VOSviewer-native density visualization.",
        "- Keyword synonym mapping, database coverage, search strategy, and cluster interpretation should be checked before publication.",
        "- Do not interpret co-occurrence as causality or as proof of a substantive relationship.",
        "",
    ]
    if "Zotero CSV" in set(records.get("database", pd.Series(dtype=str)).astype(str)):
        lines += [
            "", "## 7. Zotero export notes", "",
            "- Zotero's exported `Keywords` field may combine imported bibliographic keywords and user-created tags. Recognized library/collection labels, P1/P2/P3 tags, numbered topic labels, and star ratings were moved to `zotero_tags`; remaining terms are treated as candidate bibliographic keywords.",
            "- Review `tables/zotero_tags.csv` and `tables/record_keywords.csv` before interpreting or publishing the network; the remaining terms are not guaranteed to be a pure author-keyword field.",
            "- This Zotero CSV does not contain the full cited-reference list. It therefore cannot support co-citation or bibliographic-coupling networks. Any cited-by count parsed from `Extra` is a separate, source-specific metric.",
        ]
    output_path.write_text("\n".join(lines), encoding="utf-8")
