from pathlib import Path

from scimap_agent.io import load_bibliography
from scimap_agent.analysis import prepare_records, build_keyword_network

ROOT = Path(__file__).resolve().parents[1]


def test_wos_parser_and_network():
    records = load_bibliography(ROOT / "data" / "sample" / "synthetic_wos.txt")
    prepared = prepare_records(records, thesaurus_path=ROOT / "config" / "thesaurus.csv")
    graph, nodes, edges = build_keyword_network(prepared, min_occurrences=2)
    assert len(prepared) == 6
    assert graph.number_of_nodes() >= 4
    assert "machine learning" in graph.nodes
    assert not nodes.empty
    assert set(edges.columns) == {"source", "target", "weight"}
