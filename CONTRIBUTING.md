# Contributing to SciMap-Agent

Thanks for helping improve open, reproducible bibliometric mapping.

1. Open an issue describing the observed behavior, input format and expected result. **Do not upload private bibliographies, full-text PDFs, unpublished manuscripts or personal information**. Construct a short synthetic reproduction instead.
2. Make a focused branch; include tests for parser, terminology, plotting, or documentation changes.
3. Run `python -m pytest -q` after installing dependencies with `python -m pip install -r requirements.txt` and `python -m pip install -e .`.
4. Explain changes to scientific meaning (frequency counting, clustering, threshold, plot scale) and update the method/output docs when appropriate.
5. Submit a pull request with a concise changelog and example figure if visual output changes.

The project is MIT licensed. Contributions are submitted under that license unless explicitly agreed otherwise. Do not include commercial font files or copyrighted third-party imagery. CiteSpace native algorithm claims must be backed by a validated implementation.
