from pathlib import Path

import pandas as pd

from scimap_agent.io import load_bibliography


def test_zotero_csv_separates_organizational_tags(tmp_path: Path):
    source = tmp_path / "zotero_export.csv"
    pd.DataFrame([{
        "ZoteroKey": "ABCD1234",
        "ItemType": "journalArticle",
        "Title": "Carbon emissions in oil refineries",
        "Authors": "Smith, A; Jones, B",
        "Year": "2024",
        "Source": "Energy",
        "DOI": "10.1000/example",
        "Abstract": "A short abstract.",
        "Keywords": "carbon emissions; oil refinery; P1-驱动与数据方法主线; 04.01-历史演变与预测; ⭐⭐⭐⭐⭐",
        "Language": "en",
        "Extra": "Total Times Cited: 12",
    }]).to_csv(source, index=False, encoding="utf-8-sig")

    frame = load_bibliography(source)
    assert len(frame) == 1
    row = frame.iloc[0]
    assert row["database"] == "Zotero CSV"
    assert row["source"] == "Energy"
    assert "carbon emissions" in row["author_keywords"]
    assert "P1-驱动与数据方法主线" in row["zotero_tags"]
    assert "⭐⭐⭐⭐⭐" in row["zotero_tags"]
    assert row["citations"] == "12"
