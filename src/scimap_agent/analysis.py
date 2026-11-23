from __future__ import annotations

import itertools
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import networkx as nx
import pandas as pd

KEYWORD_SPLIT_RE = re.compile(r"\s*;\s*|\s*\|\s*|\s*\n\s*")


def normalize_keyword(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"^[\W_]+|[\W_]+$", "", value, flags=re.UNICODE)
    value = re.sub(r"\s+", " ", value)
    return value


def load_thesaurus(path: str | Path | None) -> dict[str, str]:
    if path is None or not Path(path).exists():
        return {}
    df = pd.read_csv(path, dtype=str).fillna("")
    if not {"term", "replace_by"}.issubset({c.casefold() for c in df.columns}):
        raise ValueError("Thesaurus CSV must contain columns: term, replace_by")
    cols = {c.casefold(): c for c in df.columns}
    return {
        normalize_keyword(row[cols["term"]]): normalize_keyword(row[cols["replace_by"]])
        for _, row in df.iterrows()
        if normalize_keyword(row[cols["term"]]) and normalize_keyword(row[cols["replace_by"]])
    }


def _parse_keywords(row: pd.Series, thesaurus: dict[str, str], stopwords: set[str]) -> list[str]:
    if str(row.get('term_source', '')).startswith('title'):
        raw = str(row.get('extracted_terms', ''))
    else:
        raw = f"{row.get('author_keywords', '')}; {row.get('index_keywords', '')}"
    terms = []
    for token in KEYWORD_SPLIT_RE.split(raw):
        term = normalize_keyword(token)
        if not term or term in stopwords or len(term) < 2:
            continue
        term = thesaurus.get(term, term)
        if term and term not in stopwords:
            terms.append(term)
    # Preserve first-seen order while removing within-record duplicates.
    return list(dict.fromkeys(terms))


def prepare_records(records: pd.DataFrame, thesaurus_path: str | Path | None = None,
                    stopwords_path: str | Path | None = None) -> pd.DataFrame:
    df = records.copy().fillna("")
    thesaurus = load_thesaurus(thesaurus_path)
    stopwords = set()
    if stopwords_path and Path(stopwords_path).exists():
        stopwords = {normalize_keyword(x) for x in Path(stopwords_path).read_text(encoding="utf-8").splitlines() if x.strip()}
    df["year_num"] = pd.to_numeric(df["year"].astype(str).str.extract(r"(19\d{2}|20\d{2})", expand=False), errors="coerce")
    df["citations_num"] = pd.to_numeric(df["citations"], errors="coerce")
    df["keywords"] = df.apply(lambda row: _parse_keywords(row, thesaurus, stopwords), axis=1)
    # Deduplicate by DOI where possible; otherwise use normalized title + year.
    doi_key = df["doi"].astype(str).str.casefold().str.strip().str.replace(r"^https?://(dx\.)?doi\.org/", "", regex=True)
    title_key = (df["title"].astype(str).map(lambda x: unicodedata.normalize("NFKC", x)).str.casefold().str.replace(r"[^\w]+", "", regex=True))
    fallback_key = title_key + "_" + df["year_num"].fillna(0).astype(int).astype(str)
    fallback_key = fallback_key.where(title_key.ne(""), df["record_id"].astype(str).str.casefold())
    df["_dedup_key"] = doi_key.where(doi_key.ne(""), fallback_key)
    before = len(df)
    df = df.drop_duplicates(subset="_dedup_key", keep="first").drop(columns="_dedup_key").reset_index(drop=True)
    df.attrs["duplicates_removed"] = before - len(df)
    return df



def suggest_min_occurrences(record_count: int) -> int:
    """Choose a simple exploratory threshold near 2% of the corpus size.

    The threshold is rounded to the nearest integer and never falls below 2.
    It is a convenience default for map readability, not a statistical law;
    users should report and sensitivity-check alternative thresholds.
    """
    import math

    n = max(int(record_count), 0)
    return max(2, int(math.floor(n * 0.02 + 0.5)))

def build_keyword_network(records: pd.DataFrame, min_occurrences: int = 3,
                           max_keywords: int = 500) -> tuple[nx.Graph, pd.DataFrame, pd.DataFrame]:
    """Build document-level keyword co-occurrence network and item/edge tables."""
    if min_occurrences < 1:
        raise ValueError("min_occurrences must be >= 1")
    occurrence_docs: Counter[str] = Counter()
    year_values: dict[str, list[float]] = defaultdict(list)
    paper_terms: list[list[str]] = []

    for _, row in records.iterrows():
        terms = row.get("keywords", [])
        if not isinstance(terms, list):
            terms = []
        paper_terms.append(terms)
        for term in terms:
            occurrence_docs[term] += 1
            year = row.get("year_num")
            if pd.notna(year):
                year_values[term].append(float(year))

    eligible = {term for term, count in occurrence_docs.items() if count >= min_occurrences}
    ranked = sorted(eligible, key=lambda t: (-occurrence_docs[t], t))[:max_keywords]
    eligible = set(ranked)
    pair_counts: Counter[tuple[str, str]] = Counter()
    for terms in paper_terms:
        selected = sorted(set(terms) & eligible)
        for a, b in itertools.combinations(selected, 2):
            pair_counts[(a, b)] += 1

    graph = nx.Graph()
    for term in ranked:
        years = year_values.get(term, [])
        graph.add_node(term,
                       occurrences=int(occurrence_docs[term]),
                       avg_year=(sum(years) / len(years)) if years else None)
    for (a, b), weight in pair_counts.items():
        if weight > 0:
            graph.add_edge(a, b, weight=int(weight))

    if graph.number_of_nodes() > 1 and graph.number_of_edges() > 0:
        communities = list(nx.community.greedy_modularity_communities(graph, weight="weight"))
        communities.sort(key=lambda c: (-len(c), sorted(c)[0]))
        cluster_map = {node: idx + 1 for idx, community in enumerate(communities) for node in community}
    else:
        cluster_map = {node: 1 for node in graph.nodes}

    for node, cluster_id in cluster_map.items():
        graph.nodes[node]["cluster"] = cluster_id

    if graph.number_of_nodes():
        weighted_degree = dict(graph.degree(weight="weight"))
        degree = dict(graph.degree())
        if graph.number_of_nodes() <= 500:
            betweenness = nx.betweenness_centrality(graph, weight=None, normalized=True)
        else:
            betweenness = {node: 0.0 for node in graph.nodes}
    else:
        weighted_degree, degree, betweenness = {}, {}, {}

    node_rows = []
    for term, data in graph.nodes(data=True):
        node_rows.append({
            "keyword": term,
            "occurrences": data["occurrences"],
            "links": degree.get(term, 0),
            "total_link_strength": weighted_degree.get(term, 0),
            "avg_publication_year": data["avg_year"],
            "cluster": cluster_map.get(term, 1),
            "betweenness_centrality": betweenness.get(term, 0.0),
        })
    nodes = pd.DataFrame(node_rows).sort_values(["occurrences", "keyword"], ascending=[False, True]) if node_rows else pd.DataFrame(columns=["keyword", "occurrences", "links", "total_link_strength", "avg_publication_year", "cluster", "betweenness_centrality"])

    edge_rows = [{"source": a, "target": b, "weight": d["weight"]} for a, b, d in graph.edges(data=True)]
    edges = pd.DataFrame(edge_rows).sort_values("weight", ascending=False) if edge_rows else pd.DataFrame(columns=["source", "target", "weight"])
    return graph, nodes, edges
