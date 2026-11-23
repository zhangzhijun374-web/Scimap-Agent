from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Iterable

import pandas as pd

CANONICAL_COLUMNS = [
    "record_id", "title", "year", "source", "doi", "abstract",
    "authors", "author_keywords", "index_keywords", "citations", "database",
    "item_type", "language", "zotero_tags", "extra"
]


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "gb18030", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="replace")


def _clean_scalar(value):
    if pd.isna(value):
        return ""
    return str(value).strip()


def _split_wos_records(text: str) -> list[dict[str, str]]:
    """Parse Clarivate tagged plain-text exports (one record ends with ER)."""
    records: list[dict[str, str]] = []
    current: dict[str, list[str]] = {}
    active_tag: str | None = None

    def flush():
        nonlocal current, active_tag
        if current:
            records.append({k: " ".join(v).strip() for k, v in current.items()})
        current = {}
        active_tag = None

    for raw_line in text.splitlines():
        line = raw_line.rstrip("\r\n")
        if not line.strip():
            continue
        if line.startswith("ER"):
            flush()
            continue
        if line.startswith("EF"):
            flush()
            break
        match = re.match(r"^([A-Z0-9]{2})\s+(.*)$", line)
        if match:
            tag, value = match.group(1), match.group(2).strip()
            active_tag = tag
            current.setdefault(tag, []).append(value)
        elif line.startswith("   ") and active_tag:
            continuation = line.strip()
            if continuation:
                current[active_tag].append(continuation)
    flush()
    return records


def _wos_to_frame(path: Path) -> pd.DataFrame:
    raw_records = _split_wos_records(_read_text(path))
    rows = []
    for i, r in enumerate(raw_records, start=1):
        rows.append({
            "record_id": r.get("UT", f"WOS-{i}"),
            "title": r.get("TI", ""),
            "year": r.get("PY", ""),
            "source": r.get("SO", ""),
            "doi": r.get("DI", ""),
            "abstract": r.get("AB", ""),
            "authors": r.get("AU", ""),
            "author_keywords": r.get("DE", ""),
            "index_keywords": r.get("ID", ""),
            "citations": r.get("TC", ""),
            "database": "Web of Science",
        })
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def _find_column(columns: Iterable[str], candidates: Iterable[str]) -> str | None:
    lookup = {re.sub(r"[^a-z0-9]", "", str(c).casefold()): str(c) for c in columns}
    for candidate in candidates:
        key = re.sub(r"[^a-z0-9]", "", candidate.casefold())
        if key in lookup:
            return lookup[key]
    return None


def _scopus_to_frame(path: Path) -> pd.DataFrame:
    df = None
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "gb18030", "latin-1"):
        try:
            df = pd.read_csv(path, dtype=str, encoding=encoding).fillna("")
            break
        except Exception as exc:  # try the next common export encoding
            last_error = exc
    if df is None:
        raise ValueError(f"Could not read CSV file {path}: {last_error}")

    mapping = {
        "record_id": ["EID", "Record ID", "UT"],
        "title": ["Title", "Document Title"],
        "year": ["Year", "Publication Year"],
        "source": ["Source title", "Source Title", "Publication Name", "Journal", "Source"],
        "doi": ["DOI"],
        "abstract": ["Abstract"],
        "authors": ["Authors", "Author Full Names"],
        "author_keywords": ["Author Keywords", "Author keyword", "DE", "Keywords"],
        "index_keywords": ["Index Keywords", "Indexed Keywords", "Keywords Plus", "ID"],
        "citations": ["Cited by", "Times Cited", "TC"],
    }
    out = pd.DataFrame(index=df.index)
    for target, candidates in mapping.items():
        col = _find_column(df.columns, candidates)
        out[target] = df[col].map(_clean_scalar) if col else ""
    out["record_id"] = out["record_id"].where(out["record_id"].ne(""), [f"SCOPUS-{i+1}" for i in range(len(out))])
    out["database"] = "Scopus"
    for col in CANONICAL_COLUMNS:
        if col not in out.columns:
            out[col] = ""
    return out[CANONICAL_COLUMNS]



_ZOTERO_ORG_TAG_PATTERNS = [
    re.compile(r"^炼厂碳排放驱动时序情景综述文献库$"),
    re.compile(r"^碳排放综述_对标\d+$"),
    re.compile(r"^P\d+[-－].+$", re.IGNORECASE),
    re.compile(r"^0\d(?:\.\d+)?[-－].+$"),
    re.compile(r"^[⭐★☆]+$"),
]


def _is_zotero_organizational_tag(value: str) -> bool:
    value = value.strip()
    return any(pattern.match(value) for pattern in _ZOTERO_ORG_TAG_PATTERNS)


def _extract_zotero_citation_count(extra: str) -> str:
    """Extract a cited-by count from Zotero Extra when a WOS count is present."""
    patterns = [
        r"Total Times Cited:\s*(\d+)",
        r"Times Cited in Web of Science Core Collection:\s*(\d+)",
        r"Times Cited:\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, extra or "", flags=re.IGNORECASE)
        if match:
            return match.group(1)
    return ""


def _zotero_to_frame(path: Path) -> pd.DataFrame:
    """Parse Zotero CSV exports while keeping user-created tags separate from keywords."""
    df = None
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(path, dtype=str, encoding=encoding, keep_default_na=False)
            break
        except Exception as exc:
            last_error = exc
    if df is None:
        raise ValueError(f"Could not read Zotero CSV {path}: {last_error}")

    required = {"ZoteroKey", "ItemType", "Title"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"Not a recognized Zotero CSV export: missing {sorted(required - set(df.columns))}")

    rows = []
    for i, row in df.iterrows():
        raw_keywords = _clean_scalar(row.get("Keywords", ""))
        tokens = [token.strip() for token in re.split(r"[;；|\n]+", raw_keywords) if token.strip()]
        zotero_tags = [token for token in tokens if _is_zotero_organizational_tag(token)]
        bibliographic_keywords = [token for token in tokens if not _is_zotero_organizational_tag(token)]
        extra = _clean_scalar(row.get("Extra", ""))
        rows.append({
            "record_id": _clean_scalar(row.get("ZoteroKey", "")) or f"ZOTERO-{i+1}",
            "title": _clean_scalar(row.get("Title", "")),
            "year": _clean_scalar(row.get("Year", "")) or _clean_scalar(row.get("Date", "")),
            "source": _clean_scalar(row.get("Source", "")),
            "doi": _clean_scalar(row.get("DOI", "")),
            "abstract": _clean_scalar(row.get("Abstract", "")),
            "authors": _clean_scalar(row.get("Authors", "")),
            "author_keywords": "; ".join(bibliographic_keywords),
            "index_keywords": "",
            "citations": _extract_zotero_citation_count(extra),
            "database": "Zotero CSV",
            "item_type": _clean_scalar(row.get("ItemType", "")),
            "language": _clean_scalar(row.get("Language", "")),
            "zotero_tags": "; ".join(zotero_tags),
            "extra": extra,
        })
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)

def _ris_to_frame(path: Path) -> pd.DataFrame:
    text = _read_text(path)
    records: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = {}
    for line in text.splitlines():
        m = re.match(r"^([A-Z0-9]{2})\s+-\s+(.*)$", line)
        if m:
            tag, value = m.group(1), m.group(2).strip()
            if tag == "TY" and current:
                records.append(current)
                current = {}
            current.setdefault(tag, []).append(value)
            if tag == "ER":
                records.append(current)
                current = {}
    if current:
        records.append(current)

    def joined(r, tags):
        vals = []
        for tag in tags:
            vals.extend(r.get(tag, []))
        return "; ".join(vals)

    rows = []
    for i, r in enumerate(records, start=1):
        rows.append({
            "record_id": joined(r, ["ID"]) or f"RIS-{i}",
            "title": joined(r, ["TI", "T1"]),
            "year": joined(r, ["PY", "Y1"]),
            "source": joined(r, ["JO", "JF", "T2"]),
            "doi": joined(r, ["DO"]),
            "abstract": joined(r, ["AB", "N2"]),
            "authors": joined(r, ["AU", "A1"]),
            "author_keywords": joined(r, ["KW"]),
            "index_keywords": "",
            "citations": "",
            "database": "RIS",
        })
    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def _xlsx_to_frame(path: Path) -> pd.DataFrame:
    """Import a master bibliography XLSX through a safe read-only OOXML parser."""
    from .xlsx_reader import read_sheet_rows
    rows = read_sheet_rows(path)
    if not rows:
        raise ValueError('No bibliography rows in the selected workbook sheet')
    headers = [str(x or '').strip() for x in rows[0]]
    def cell(record, name):
        idx = headers.index(name) if name in headers else -1
        return record[idx] if idx >= 0 and idx < len(record) else ''
    if 'Title' not in headers or 'Year' not in headers:
        raise ValueError('Excel master sheet must have Title and Year columns')
    group_headers = ['Total literature', 'Carbon emissions', 'Refinery carbon emissions',
                     'ML + carbon emissions', 'ML + refinery carbon emissions']
    output = []
    for i, values in enumerate(rows[1:], 1):
        title = str(cell(values, 'Title') or '').strip()
        if not title:
            continue
        record = {
            'record_id': str(cell(values, 'ID') or f'XLSX-{i}'),
            'title': title,
            'year': str(cell(values, 'Year') or ''),
            'source': str(cell(values, 'Journal / organization') or cell(values,'Journal') or ''),
            'doi': str(cell(values, 'DOI') or ''),
            'abstract': str(cell(values,'Abstract') or ''),
            'authors': str(cell(values,'Authors') or ''),
            'author_keywords': str(cell(values,'Author Keywords') or ''),
            'index_keywords': str(cell(values,'Index Keywords') or ''),
            'citations': '', 'database': 'Excel master bibliography',
            'item_type': str(cell(values,'Record type') or ''),
            'language': '', 'zotero_tags': '', 'extra': '',
        }
        for group in group_headers:
            if group in headers:
                record[group] = int(str(cell(values, group) or '0') in {'1','1.0','True'})
        output.append(record)
    return pd.DataFrame(output)


def load_bibliography(path: str | Path) -> pd.DataFrame:
    """Load Zotero CSV, WoS tagged TXT, Scopus CSV, or RIS into a canonical schema."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(path)
    suffix = path.suffix.casefold()
    if suffix == ".xlsx":
        return _xlsx_to_frame(path)
    if suffix in {".csv"}:
        # Zotero exports have a distinctive schema and must not be treated as Scopus CSV.
        try:
            header = pd.read_csv(path, nrows=0, encoding="utf-8-sig").columns
        except Exception:
            header = []
        if {"ZoteroKey", "ItemType", "Title"}.issubset(set(header)):
            return _zotero_to_frame(path)
        return _scopus_to_frame(path)
    if suffix in {".ris"}:
        return _ris_to_frame(path)
    if suffix in {".txt", ".ciw", ".wos"}:
        frame = _wos_to_frame(path)
        if frame.empty:
            raise ValueError(f"No WoS records were parsed from {path}. Check that it is a tagged plain-text export.")
        return frame
    raise ValueError(f"Unsupported file type: {suffix}. Supported formats: Zotero CSV, Scopus CSV, WoS TXT, RIS.")


def load_inputs(input_path: str | Path) -> pd.DataFrame:
    """Load one file or every supported file in a directory."""
    path = Path(input_path)
    if path.is_file():
        return load_bibliography(path)
    if not path.is_dir():
        raise FileNotFoundError(path)
    files = sorted(p for p in path.iterdir() if p.is_file() and p.suffix.casefold() in {".csv", ".txt", ".ciw", ".wos", ".ris", ".xlsx"})
    if not files:
        raise ValueError(f"No supported bibliography files found in {path}")
    frames = [load_bibliography(p) for p in files]
    return pd.concat(frames, ignore_index=True)
