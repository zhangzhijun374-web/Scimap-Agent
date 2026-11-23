from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from .analysis import build_keyword_network, prepare_records, suggest_min_occurrences
from .io import load_inputs
from .report import write_report
from .visualize import export_visuals


def run_analysis(args) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    import pandas as pd
    from .io import load_bibliography
    from .extended_analysis import enrich_records_with_metadata
    if input_path.is_dir():
        xlsx_files = sorted(input_path.glob('*.xlsx'))
        other_files = sorted(p for p in input_path.iterdir() if p.is_file() and p.suffix.casefold() in {'.csv','.ris','.txt','.ciw','.wos'})
        if len(xlsx_files) == 1 and other_files:
            raw = load_bibliography(xlsx_files[0])
            extra = pd.concat([load_bibliography(p) for p in other_files],ignore_index=True)
            raw = enrich_records_with_metadata(raw,extra)
        else:
            raw = load_inputs(input_path)
    else:
        raw = load_inputs(input_path)
    if args.enrich_with:
        additional = load_inputs(Path(args.enrich_with))
        raw = enrich_records_with_metadata(raw,additional)
        print('Enrichment:', raw.attrs.get('enrichment',{}))
    if args.publication_type == 'journal':
        is_journal=raw['item_type'].astype(str).str.casefold().isin({'jour','journalarticle','journal','article','article-journal'})
        raw=raw.loc[is_journal].copy()
        if raw.empty: raise ValueError('No journal records under this publication-type filter')
    supported = {".csv", ".txt", ".ciw", ".wos", ".ris", ".xlsx"}
    input_files = [str(input_path)] if input_path.is_file() else [str(p) for p in sorted(input_path.iterdir()) if p.is_file() and p.suffix.casefold() in supported]
    from .extended_analysis import GROUPS, run_comparative, resolve_term_source, prepare_with_terms
    if any(name in raw.columns for name, _, _ in GROUPS):
        run_comparative(raw, output_path, args)
        return 0
    mode = resolve_term_source(raw,args.term_source)
    records = prepare_with_terms(raw, mode, args.thesaurus, args.stopwords, args.title_rules)
    min_occurrences = (
        suggest_min_occurrences(len(records))
        if str(args.min_occurrences).casefold() == "auto"
        else int(args.min_occurrences)
    )
    graph, nodes, edges = build_keyword_network(records, min_occurrences=min_occurrences, max_keywords=args.max_keywords)

    tables_dir = output_path / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)
    records.drop(columns=["keywords"], errors="ignore").to_csv(tables_dir / "normalized_records.csv", index=False, encoding="utf-8-sig")
    records[["record_id", "title", "year", "keywords"]].assign(keywords=records["keywords"].map(lambda x: "; ".join(x))).to_csv(tables_dir / "record_keywords.csv", index=False, encoding="utf-8-sig")
    if "zotero_tags" in records.columns:
        tag_rows = []
        for _, row in records.iterrows():
            for tag in str(row.get("zotero_tags", "") or "").split(";"):
                tag = tag.strip()
                if tag:
                    tag_rows.append({"record_id": row.get("record_id", ""), "title": row.get("title", ""), "zotero_tag": tag})
        pd.DataFrame(tag_rows, columns=["record_id", "title", "zotero_tag"]).to_csv(tables_dir / "zotero_tags.csv", index=False, encoding="utf-8-sig")

    from .extended_analysis import keyword_frequency, year_term_counts, draw_timeline
    freqs = keyword_frequency(records)
    freqs.to_csv(tables_dir / "keyword_frequency_all.csv", index=False, encoding="utf-8-sig")
    freqs.loc[freqs["occurrences"] >= min_occurrences].head(10).to_csv(tables_dir / "top10_keywords.csv", index=False, encoding="utf-8-sig")
    year_term_counts(records).to_csv(tables_dir / "keyword_year_counts.csv", index=False, encoding="utf-8-sig")
    paths = export_visuals(graph, nodes, output_path, max_labels=args.max_labels, dpi=args.dpi)
    draw_timeline(records, freqs, output_path / "figures" / "keyword_timeline.png", dpi=args.dpi)
    report_path = output_path / "reports" / "analysis_report.md"
    parameters = {"min_occurrences": min_occurrences, "min_occurrences_mode": str(args.min_occurrences), "max_keywords": args.max_keywords, "max_labels": args.max_labels, "dpi": args.dpi, "community_detection": "NetworkX greedy modularity", "layout": "ForceAtlas2 with compact component packing (spring-layout fallback)", "visualization_style": "journal-cluster-times600 (Times-style typography, enlarged nodes/labels, stronger curved links, collision-relaxed labels)", "counting": "full counting / document-level binary", "term_source": mode, "publication_type": args.publication_type}
    write_report(records, nodes, edges, report_path, input_files=input_files, parameters=parameters)
    metadata = {"created_utc": datetime.now(timezone.utc).isoformat(), "input_files": input_files, "records_after_deduplication": int(len(records)), "duplicates_removed": int(records.attrs.get("duplicates_removed", 0)), "network_nodes": int(graph.number_of_nodes()), "network_edges": int(graph.number_of_edges()), "parameters": parameters}
    (output_path / "run_metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print("SciMap-Agent analysis complete")
    print(f"Records: {len(records)} | Keywords: {graph.number_of_nodes()} | Links: {graph.number_of_edges()}")
    print(f"Report: {report_path}")
    print(f"Figures: {paths['figures']}")
    print(f"VOSviewer exports: {paths['vosviewer']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scimap", description="Bibliometric analysis and scientific knowledge mapping")
    sub = parser.add_subparsers(dest="command", required=True)
    analyze = sub.add_parser("analyze", help="Analyze Zotero CSV, WoS TXT, Scopus CSV, or RIS files")
    analyze.add_argument("--input", required=True, help="A bibliography file or a folder containing supported files")
    analyze.add_argument("--output", default="outputs", help="Output folder (default: outputs)")
    analyze.add_argument("--min-occurrences", default="auto", help="Minimum documents per keyword; auto = about 2%% of corpus size (minimum 2), or provide an integer (default: auto)")
    analyze.add_argument("--max-keywords", type=int, default=500, help="Maximum number of keywords in network (default: 500)")
    analyze.add_argument("--max-labels", type=int, default=None, help="Optional label cap; by default the publication style selects labels automatically")
    analyze.add_argument("--term-source", choices=["auto", "bibliographic", "title", "title_abstract"], default="auto", help="Term provenance: original bibliographic keywords or inferred controlled title/abstract terms")
    analyze.add_argument("--enrich-with", default=None, help="Optional bibliography export providing missing abstracts and keywords (matched by DOI/title)")
    analyze.add_argument("--publication-type", choices=["all","journal"], default="all", help="Select all records or journal publications only (default: all)")
    analyze.add_argument("--title-rules", default="config/title_term_patterns.csv", help="Optional CSV with term,pattern columns for transparent title/abstract vocabulary extraction")
    analyze.add_argument("--dpi", type=int, default=600, help="Figure resolution (default: 600 dpi)")
    analyze.add_argument("--thesaurus", default="config/thesaurus.csv", help="Optional synonym mapping CSV")
    analyze.add_argument("--stopwords", default="config/stopwords.txt", help="Optional newline-separated stopword list")
    analyze.set_defaults(func=run_analysis)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
