# Installation and first run / 安装和首次使用

> Tested core: Python 3.10–3.12 in GitHub Actions configuration; local tests also pass in the build environment. Windows *dialog* workflows require an actual Windows installation to verify UI behavior.

## Windows (recommended for non-programmers)

1. Download the repository ZIP or clone your repository; extract it to a normal writable directory.
2. Install Python **3.11** with the `py` launcher.
3. Double-click `Install-SciMap-Agent.bat`. It creates `.venv` and installs dependencies; network access is needed to download packages.
4. Double-click `Start-SciMap-Agent.bat` and select one or more `.csv`, `.txt`, `.ciw`, `.wos`, `.ris`, or `.xlsx` metadata exports. Select where to save results.
5. If Windows has restricted PowerShell scripts, start PowerShell **in the project root** and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\install_windows.ps1
powershell -ExecutionPolicy Bypass -File .\run_analysis_windows.ps1
```

The file picker temporarily copies the selected files to a temporary directory and removes that copy after analysis. The original source files are not overwritten. Review what is selected: mixing an XLSX master workbook with other metadata exports triggers automatic DOI/title enrichment logic when exactly one workbook is present.

## Command-line install (Windows / macOS / Linux)

From the repository root:

```bash
python -m venv .venv
# Windows: .venv\Scripts\python -m pip install -e .
# macOS/Linux:
.venv/bin/python -m pip install -e .
.venv/bin/scimap analyze --input data/sample/synthetic_wos.txt --output outputs/synthetic-demo --min-occurrences 2
```

To test the package (with pytest installed):

```bash
python -m pip install -r requirements.txt
python -m pip install -e .
python -m pytest -q
```

If `scimap` is not on your PATH, run `python -m scimap_agent.cli analyze ...` using the interpreter in the virtual environment.

## CLI arguments

| Flag | Meaning |
|---|---|
| `--input` | Single bibliography file or directory with supported exports |
| `--output` | Result directory |
| `--min-occurrences` | Minimum number of documents per term; `auto` for ordinary corpora |
| `--term-source auto` | Choose original keyword fields when coverage is sufficient; else inferred title/abstract terms |
| `--term-source bibliographic` | Force original keyword fields (requires nonempty data) |
| `--term-source title` | Infer controlled terms from titles only |
| `--term-source title_abstract` | Infer controlled terms from titles and abstracts |
| `--enrich-with PATH` | Fill missing abstract/keyword metadata from another export, matched by DOI or exact normalized title |
| `--publication-type journal` | Keep recognized journal entries only |
| `--dpi 600` | PNG raster resolution (PDF and SVG are vector files) |
| `--max-keywords`, `--max-labels` | Network term and label caps |
| `--title-rules`, `--thesaurus`, `--stopwords` | Explicit custom vocabularies; see `config/` |

Run `scimap analyze --help` for the installed CLI's authoritative options.

## Troubleshooting / 常见问题

- **`py -3.11` not found:** Install Python 3.11 and its launcher; if using another supported Python release, create the venv manually.
- **Cannot run PowerShell:** Use the explicit PowerShell commands above, or run the Python CLI directly.
- **`No keywords meet threshold`:** Reduce `--min-occurrences` for an exploratory run, and confirm the data contain suitable keyword fields or valid title patterns.
- **Wrong labels in Zotero:** Review `zotero_tags.csv`, keyword tables and `config/` rules; automatic label detection is imperfect.
- **Times New Roman not displayed:** Install the font in the OS; the project does not ship fonts. Non-Windows platforms may use a Times-like fallback.
- **Figures clipped or overlapping:** Review the SVG and the source data at the actual manuscript size; automatic layout is not a guarantee of perfect typography in every corpus.
- **Memory/time limits:** Start with a small representative input or reduce the maximum network keywords. `600 dpi` PNG output, especially dense graphs, can use significant memory.
- **Need exact CiteSpace timelines/bursts/co-citation?** Not implemented. This is a NetworkX-based metadata mapping tool, not a CiteSpace API bridge.
