# Methods, interpretation and limitations / 方法学与适用边界

## Data preparation

Bibliographic records are normalized by the parsers in `io.py`. Duplicate references are identified using DOI/title evidence. User-defined stopword and thesaurus files help standardize terms; neither step establishes scientific synonymy by itself. Preserve the raw export in an independent, private location to make the data processing traceable.

## Keyword/term selection

Term provenance is explicitly recorded as either (a) supplied author/index/database keywords or (b) **controlled terms inferred** with regular-expression rules from titles or titles+abstracts. The latter is an analytical proxy and can be subject to vocabulary bias. It is not equivalent to extracting authors' chosen keywords. Terms are counted at the document level using full counting: one occurrence per document per normalized term, even if the string appears multiple times in the text.

## Network and communities

- **Nodes** are normalized terms that meet the minimum-document frequency threshold.
- An **edge** connects terms co-occurring within at least one bibliographic record; weight reflects document-level co-occurrence count.
- Community assignment is performed using weighted NetworkX greedy modularity.
- Node layouts are computed via NetworkX ForceAtlas2 when available or a spring-layout fallback. Small disconnected components may be packed visually near the largest component, without fabricating graph edges.
- Ellipse contours and cluster headings are **visual aids**; ellipse intersection or label placement is not a statistical test. Cluster headings come from the highest-frequency non-overlapping terms and require editorial review.
- Node sizes encode frequency, and edge widths encode co-occurrence weight; apparent distance should not be interpreted as a calibrated physical or semantic distance.

## Temporal statistics

- **Average-publication-year overlay:** a node's mean associated publication year; this is not a trend regression.
- **Annual term heatmap:** the number of documents in each year that include the term.
- **Cluster timeline:** representative terms grouped by detected community, with annual dots scaled by counts. This is a custom visualization, **not a CiteSpace native timeline, Kleinberg burst algorithm or time-zone visualization**.
- **Two-panel overlay (recognized XLSX):** the current implementation favors a refinery-emissions group and an ML+carbon-emissions group. A consistent **2016–2026** colorbar with 2-year ticks is used for display; years earlier/later are color-clipped. Edge colors blend between the endpoint-node colors along curved segments. This blended color is visual style, not an independent quantity.

## Parameter disclosure (paper writing)

For a manuscript, report at minimum: bibliographic sources and retrieval dates, the actual full search queries, initial and deduplicated record counts, inclusion/exclusion criteria, input field coverage, whether analyzed terms came from *author keywords* or *title/abstract inference*, synonym/stopword dictionary, minimum frequency, weighting/full-counting, community algorithm, software name/version, and time coverage. Validate automatic category labels and inspect whether the final year is incomplete.

Suggested methods wording **only if it matches the run used in your article**:

> Bibliographic metadata were cleaned and deduplicated before document-level full-counting term co-occurrence analysis in SciMap-Agent (v0.4.3). Communities were identified using NetworkX weighted greedy modularity, and the network layout used ForceAtlas2 with spring-layout fallback. Term frequencies represented the number of documents containing each normalized term; temporal plots summarized annual document counts and average associated publication year. Analysis settings, term provenance, data coverage and any category-screening limitations were recorded in the output files.

If the corpus uses title-inferred controlled terms, explicitly replace “keyword co-occurrence” with **“controlled title-term co-occurrence”**. Do not call either cluster timeline “CiteSpace analysis” unless independently performed within CiteSpace.

## Limitations

1. This is metadata mapping, not full-text content analysis or a validated systematic review.
2. Co-occurrence networks are descriptive correlations and do not identify causal relationships, transitions, or mechanisms.
3. Modularity clusters depend on vocabulary, corpus selection, graph threshold and algorithm.
4. Automatic cluster titles and topic flags can be semantically wrong.
5. Coverage of supplied keyword/abstract fields can vary substantially across source databases.
6. The publication-style layout, especially in dense maps, may still require journal-size readability checks.
7. The environment may not have Times New Roman; a different serif font can be used as fallback. No font is bundled.
8. The software does **not** currently implement CiteSpace native burst detection, co-citation networks or full bibliographic coupling.
9. No machine-learning model is trained merely because the bibliography contains ML-related papers; the network measures metadata terms only.
