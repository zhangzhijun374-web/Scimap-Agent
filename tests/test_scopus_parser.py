from pathlib import Path

from scimap_agent.io import load_bibliography

ROOT = Path(__file__).resolve().parents[1]


def test_scopus_csv_parser():
    frame = load_bibliography(ROOT / "data" / "sample" / "synthetic_scopus.csv")
    assert len(frame) == 2
    assert frame.loc[0, "title"] == "Machine learning in exposure science"
    assert frame.loc[0, "author_keywords"] == "machine learning; exposure science"
    assert frame.loc[0, "year"] == "2022"
