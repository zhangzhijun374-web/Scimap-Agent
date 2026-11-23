# Input formats and data provenance / 数据格式与来源

## Supported metadata exports

| Source | Supported file(s) | Notes |
|---|---|---|
| Zotero | CSV | Reads familiar Zotero export columns; heuristic filtering moves recognized organizational tags out of candidate keywords. Review uncertain tags. |
| Web of Science | TXT, CIW, WOS | Tagged record exports. Author keywords and Keywords Plus may be available; select fields available at export. |
| Scopus | CSV | Recognized titles, years, keyword columns; coverage depends on the database export options. |
| RIS | RIS | Standard citation records where supported fields exist. |
| Grouped literature workbook | XLSX | Recognized merged workbook containing a master publication sheet and the supported five research category flags. This is **not** a general-purpose arbitrary XLSX importer. |

For strongest bibliometric claims, export **title, publication year, DOI, author keywords, index/database keywords, abstract, source and document type** when available. Cited-reference lists are **not** used for co-citation in the current version.

## Missing keywords / 缺少关键词怎么办？

The selection logic in `--term-source auto` is global to the dataset:

1. Use original author/index keywords if present in a sufficient proportion of records (current threshold: 70%).
2. Otherwise, if abstract coverage is at least 70%, infer controlled terms from title+abstract.
3. Otherwise, infer controlled terms from titles alone.

The controlled dictionary and regexes live in `config/title_term_patterns.csv`. These terms are *inferred by the software* and **must not** be described as original author keywords. The available vocabulary may miss terms outside its covered subjects; review and extend it as needed.

The source detection threshold is a pragmatic rule, not a scientifically validated completeness standard. A dataset mixing different formats should be examined for biased keyword coverage.

## Matching a master workbook to richer metadata

```bash
scimap analyze --input data/raw/master.xlsx --enrich-with data/raw/full_bibliography.csv --output outputs/enriched
```

This only fills missing abstract/keyword fields, using DOI first and otherwise normalized exact title. It does not guarantee all items are matched correctly; inspect the summary's enrichment statistics and audit ambiguous titles. Do not silently overwrite existing master fields.

## Grouped XLSX comparative mode

The grouped mode recognizes a specific five-theme classification schema:

- `Total literature`
- `Carbon emissions`
- `Refinery carbon emissions`
- `ML + carbon emissions`
- `ML + refinery carbon emissions`

The importer maps recognized workbook columns to those internal flags; it does not discover arbitrary categories or guarantee machine-generated screening is correct. A record can belong to more than one group. Total counts are not additive. For small groups (under 50 documents), a lower frequency threshold (2) is used for exploratory networks and noted in reports; this prevents a very sparse/no-node map but makes cross-group comparisons more sensitive to threshold choices.

## Source and copyright considerations

Do not distribute personal citation libraries, copyrighted PDF full texts, unpublished documents, identifiable data, or publisher-restricted exports inside a public project. `data/sample/` includes *fabricated synthetic data* for demonstrations. The repository excludes `data/raw/` and `outputs/` via `.gitignore`.

The project's bibliography field parsing and keyword normalization are intentionally limited: inspect `src/scimap_agent/io.py`, `src/scimap_agent/analysis.py`, and `config/` before drawing research conclusions.
