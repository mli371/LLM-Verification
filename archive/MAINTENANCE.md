MAINTENANCE
===========

Purpose
-------
This file summarizes the current project logic (data flow, key scripts, and recommended maintenance actions) for the LLM Verification pipeline.

High-level flow
---------------
1. Prompts (canonical: `prompts/consolidated_prompts_by_topic.txt`) are used to generate LLM outputs.
2. Raw outputs are collected into `sample_data/*.jsonl` (per-run files). These are consolidated and de-duplicated into `sample_data/combined_outputs.jsonl` by `scripts/consolidate.py`.
3. `scripts/consolidate.py` produces `outputs/topic_comparison.csv` (per-topic × per-model Benford stats) and other CSVs.
4. `scripts/generate_summary_plots.py` reads `outputs/topic_comparison.csv` and writes high-level summary plots into `outputs/summary/` (chi2 heatmap and per-topic Benford overlays).
5. `llm_verification/` contains core analysis and I/O utilities (`utils.py`, `analyzer_benford.py`, `analyzer_zipf.py`, `visualize.py`, `collector.py`, `runner.py`).

Core files to keep
------------------
- llm_verification/ (all modules)
- scripts/consolidate.py
- scripts/generate_summary_plots.py
- scripts/archive_unused.py
- sample_data/combined_outputs.jsonl
- sample_data/by_topic/
- outputs/topic_comparison.csv
- outputs/topic_summary.tsv
- outputs/summary/
- prompts/consolidated_prompts_by_topic.txt
- tests/
- README.md
- requirements.txt
- .gitignore

Maintenance commands
--------------------
- Merge/refresh consolidated outputs:
  ```bash
  PYTHONPATH=. python scripts/consolidate.py
  ```

- Re-generate summary plots:
  ```bash
  python3 scripts/generate_summary_plots.py
  ```

- Run tests:
  ```bash
  pytest -q
  ```

- Archive non-core files (safe, interactive):
  ```bash
  python3 scripts/archive_unused.py  # or with --auto for non-interactive
  ```

Notes & tips
------------
- `combined_outputs.jsonl` is the canonical dataset for analysis. Backups and per-run raw JSONL files are only needed for auditing or re-processing.
- If you need Benford p-values, ensure `scipy` is installed (add to `requirements.txt`).
- Keep `outputs/summary/` up-to-date — this is the primary deliverable for quick review.
- Archive directories are safe backups; use `archive/` to restore if needed.

Contact
-------
For further changes to the maintenance policy, update this file and, if appropriate, the `scripts/final_whitelist.txt` used by the archive tool.
