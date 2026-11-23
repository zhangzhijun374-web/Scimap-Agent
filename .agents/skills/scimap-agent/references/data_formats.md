# Supported input formats

## Web of Science

Use the Clarivate plain-text tagged export. The MVP reads common tags: `UT`, `TI`, `PY`, `SO`, `DI`, `AB`, `AU`, `DE`, `ID`, and `TC`. Export records with full record details where possible.

## Scopus

Use CSV export. The MVP recognizes common columns including `EID`, `Title`, `Year`, `Source title`, `DOI`, `Abstract`, `Authors`, `Author Keywords`, `Index Keywords`, and `Cited by`.

## RIS

The MVP recognizes common RIS tags including `TI`/`T1`, `PY`/`Y1`, `JO`/`JF`/`T2`, `DO`, `AB`/`N2`, `AU`/`A1`, and `KW`.

## Limitations

CNKI Excel/Refworks/NoteExpress exports, BibTeX, PubMed XML, Dimensions, OpenAlex, and Lens exports are not yet validated. Convert them to a supported format only if field semantics are preserved; otherwise add a dedicated parser and tests.
