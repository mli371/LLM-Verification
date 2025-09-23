# LLM Verification — Project overview and quick start

This repository contains a lightweight, reproducible pipeline for verifying properties of large language model (LLM) outputs across prompts and models. The current focus is on two statistical checks commonly used to validate numeric and textual distributions:

- Benford's Law — checks the distribution of leading digits in numeric outputs.
- Zipf's Law — inspects word-frequency distributions in textual outputs.

This project supports: collection (via JSONL or API), per-response parsing (extract numbers / text), per-topic consolidation, statistical analysis (chi-square, slope/R²), and visualization.

Supported files and structure (important)

- `requirements.txt` — Python dependencies used for analysis and plotting.
- `prompts/` — canonical prompt sets organized by topic.
- `sample_data/` — canonical example datasets and per-topic exports; `sample_data/combined_outputs.jsonl` is the canonical combined dataset used by the analysis scripts.
- `llm_verification/` — core Python package containing:
  - `collector.py` — collection utilities and API client wrapper (optional OpenAI support).
  - `analyzer_benford.py` — leading-digit extraction and chi-square Benford utilities.
  - `analyzer_zipf.py` — Zipf slope and R² utilities.
  - `visualize.py` — plotting helpers used by `scripts/generate_summary_plots.py`.
  - `utils.py` — shared helpers (JSONL I/O, number/text extraction).
- `scripts/` — convenience scripts to consolidate outputs, generate summary plots, and archive legacy files (`consolidate.py`, `generate_summary_plots.py`, `archive_unused.py`).
- `outputs/` — analysis outputs and summary plots. Keep `outputs/summary/` and `outputs/topic_comparison.csv` as canonical deliverables; other files may be archived.
- `archive/` — timestamped archives of legacy outputs and auxiliary scripts (kept for reproducibility and rollback).

Quick start (macOS / zsh)

1) Create and activate a Python virtual environment, then install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2) Run tests (pytest):

```bash
pytest -q
```

3) Analyze the canonical combined dataset (example):

```bash
python -m llm_verification.analyzer_benford sample_data/combined_outputs.jsonl --out outputs/topic_comparison.csv
python -m llm_verification.analyzer_zipf sample_data/combined_outputs.jsonl --out outputs/zipf_summary.csv
```

4) Generate summary plots (reads `outputs/topic_comparison.csv`):

```bash
python scripts/generate_summary_plots.py
```

Collection & runner notes

- The runner (`llm_verification/runner.py`) supports batching with `--batch-size`, limiting prompts with `--max-prompts`, and running multiple workers. See the runner's `--help` for all flags.
- For API collection, set `OPENAI_API_KEY` (or the environment variable your provider expects). The collector records each request/response as a JSON object in JSONL so collections are reproducible and diffable.

Recommended development workflow

1. Work on prompts in `prompts/` and stage small dry-runs with `--batch-size 2` to confirm response shapes.
2. Consolidate JSONL outputs with `scripts/consolidate.py` to produce `sample_data/combined_outputs.jsonl` and `outputs/topic_comparison.csv`.
3. Run `scripts/generate_summary_plots.py` to produce `outputs/summary/` PNGs used in reports.

Deliverables and what to share with collaborators / professors

- Canonical dataset: `sample_data/combined_outputs.jsonl`
- Summary CSV: `outputs/topic_comparison.csv` (per topic & model Benford counts & chi-square)
- Summary plots: `outputs/summary/chi2_heatmap.png` and `outputs/summary/benford_by_topic_combined.png`
- Short report (draft): `report/Professor_Report.md`

Archival policy

- Non-core artifacts (many per-run PNGs, intermediate CSVs, old scripts) are archived under `archive/archive_all_<timestamp>_utc/` and can be restored if needed. Keep only canonical datasets and summary plots in `outputs/summary/` to reduce clutter.

Notes on reproducibility and costs

- Collections that call an API will incur usage costs. Use small dry-runs to estimate tokens and prefer sampling strategies for expensive models.
- All analysis scripts read JSONL and are deterministic; version-control both the prompts and the `sample_data/combined_outputs.jsonl` used for a paper or a report.

Contact / next steps

If you'd like, I can:
- produce a professor-ready PDF (from the `report/Professor_Report.md`) and a one-slide summary with the two summary plots.
- add automated CI checks to run the analyzers on a tiny dataset and ensure the code continues to work.

---
Updated: September 22, 2025