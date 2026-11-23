import json
from pathlib import Path

from scimap_agent.analysis import build_keyword_network, prepare_records
from scimap_agent.io import load_bibliography
from scimap_agent.visualize import export_visuals

ROOT = Path(__file__).resolve().parents[1]


def test_publication_style_exports_all_formats(tmp_path: Path):
    records = load_bibliography(ROOT / "data" / "sample" / "synthetic_wos.txt")
    prepared = prepare_records(
        records,
        thesaurus_path=ROOT / "config" / "thesaurus.csv",
        stopwords_path=ROOT / "config" / "stopwords.txt",
    )
    graph, nodes, _ = build_keyword_network(prepared, min_occurrences=2)
    paths = export_visuals(graph, nodes, tmp_path, dpi=100)
    figures = Path(paths["figures"])
    assert (figures / "keyword_network.png").exists()
    assert (figures / "keyword_network.svg").exists()
    assert (figures / "keyword_network.pdf").exists()
    style = json.loads((figures / "visual_style.json").read_text(encoding="utf-8"))
    assert style["name"] == "journal-cluster"
    assert "dashed" in style["clusters"]
