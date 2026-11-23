# Publish v0.4.3 to an **existing** GitHub repository / 更新已有仓库

**Publishing status:** These instructions prepare the local source; they do **not** themselves upload files to GitHub. Use the exact existing repository URL. Never create a second repository just because the expected one is not found.

## Repository release checklist

- [ ] Confirm the correct GitHub owner/repository URL and that your authenticated account has write access.
- [ ] Confirm `pyproject.toml` and package `__version__` both read **0.4.3**.
- [ ] Run the automated tests: `python -m pytest -q` after installing the package and test dependencies.
- [ ] Review staged files: only source code, documentation, MIT license, and `data/sample/` synthetic input.
- [ ] Verify original Zotero CSV, master XLSX, copyrighted PDF, personal notes, manuscript files, `data/raw/`, `.venv/` and generated `outputs/` are **not** staged.
- [ ] Inspect `README.md`, `README_CN.md`, `CHANGELOG.md`, `docs/` and `CONTRIBUTING.md`.
- [ ] Confirm README screenshots come from **synthetic** records and are labeled as such.
- [ ] Push to the existing repository's default branch and verify the remote SHA.
- [ ] Create a release tagged `v0.4.3` from the verified commit; upload a sanitized source ZIP if desired.

## Existing repository workflow (PowerShell)

```powershell
# Choose a fresh directory and clone the exact existing URL
# Replace the placeholder below with the confirmed existing URL:
git clone https://github.com/OWNER/SciMap-Agent.git
cd SciMap-Agent

# Copy the contents of the clean release source (not private data) into this checkout.
git status --short
# Verify the above output contains only intended code/documentation/synthetic examples.
git add README.md README_CN.md CHANGELOG.md LICENSE CONTRIBUTING.md `
        pyproject.toml requirements.txt .gitignore src config docs tests data/sample `
        .agents .github Install-SciMap-Agent.bat Start-SciMap-Agent.bat `
        install_windows.ps1 run_analysis_windows.ps1 run_demo.ps1

git diff --cached --stat
git diff --cached --name-only
# Double-check no raw bibliographies, personal data, binaries or proprietary sources.
git commit -m "Release SciMap-Agent v0.4.3: docs and publication-style plots"
git push origin HEAD
```

The commands above assume the original checkout has a suitable default branch. Do **not** force push. If remote changes are present, inspect/reconcile them first. The release ZIP has no `.git` history, so always copy the clean project content **into a cloned repository** rather than replacing its `.git` directory.

## Suggested GitHub repository description

`Local bibliometric analysis, keyword networks, temporal plots and publication-style SVG/PDF/600-dpi PNG output with a Codex Skill.`

Suggested topics: `bibliometrics`, `science-mapping`, `scientific-visualization`, `literature-review`, `python`, `research-tools`, `networkx`, `codex-skill`.

## Release description

**SciMap-Agent v0.4.3 — Public beta**

- Imports Zotero, WoS, Scopus, RIS, and a recognized five-group XLSX format.
- Builds document-level keyword/co-term networks, Top-10 term tables, and temporal plots.
- Exports 600-dpi PNG, vector PDF/SVG, tables, reports and VOSviewer-compatible files.
- Improves cluster typography and node visibility; adds two-panel 2016–2026 temporal overlays with curved endpoint-gradient links.
- Includes a Windows file picker and a Codex Skill.

**Limits:** Keyword/term network only; CiteSpace native burst detection, co-citation, and verified CiteSpace MCP control are *not* included. Classifications and term provenance need researcher review. Windows GUI use should be tested on a real Windows machine.
