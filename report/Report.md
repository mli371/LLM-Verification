# LLM Verification — Final Report

This report summarizes the objectives, methods, and results of the LLM Verification project. The goal is to assess whether outputs from different large language models (LLMs) and prompt types exhibit expected statistical regularities (Benford's Law for numeric outputs and Zipf's Law for textual outputs), and to highlight notable deviations that merit further investigation.

## 1. Executive summary

- Objective: quantify distributional properties of LLM outputs across topics and models to detect systematic generation artifacts or anomalies.
- Scope: consolidated dataset `sample_data/combined_outputs.jsonl` covering multiple topics and models. Analyses include per-topic/model Benford counts, chi-square statistics, and Zipf slope/R² estimates.
- Main outcome: a set of summary CSVs and plots (`outputs/topic_comparison.csv`, `outputs/summary/`) that identify topic/model pairs with elevated deviations from expected laws. These pairs are candidates for targeted follow-up experiments.

## 2. Data and preprocessing

- Collection: responses were generated from curated prompts grouped by topic and recorded as JSONL with metadata (prompt id, model, timestamp).
- Parsing: responses were tokenized and scanned for numeric strings and textual content. Numeric tokens were normalized (strip punctuation, standardize sign/format) before extracting leading digits for Benford analysis. Textual data were lowercased and tokenized for Zipf analysis.

## 3. Analysis methods

- Benford analysis: for each (topic, model) pair we counted leading digits (1–9) and computed the Pearson chi-square statistic against Benford expected proportions. Where available, p-values from the chi-square test are reported.
- Zipf analysis: for textual outputs we computed word-frequency distributions and fit a power-law (Zipf) model to estimate the slope and R².
- Visualization: generated heatmaps (chi-square per topic/model) and composite Benford plots per topic to facilitate visual inspection.

## 4. Key findings

- Overall agreement: many topic/model combinations—particularly those producing longer numeric series or narrative text—show distributions broadly consistent with Benford and Zipf expectations.
- Notable deviations: a subset of model/topic pairs exhibit significantly elevated chi-square values for Benford analysis. These deviations often correspond to prompts that elicit short, structured outputs (tables, receipts) or to outputs containing repeated formatting patterns. These are listed in `outputs/topic_comparison.csv` and visible in `outputs/summary/chi2_heatmap.png`.
- Zipf observations: narrative and review-style prompts produce heavy-tailed word-frequency distributions with slopes close to expected ranges, while highly templated prompts (e.g., CSV/table outputs) deviate due to limited vocabulary.

## 5. Recommended follow-up

1. Manual inspection: review raw responses for the highest chi-square topic/model pairs to understand the cause (formatting, enumerations, tokenization artifacts).
2. Controlled A/B testing: run targeted prompt variants to determine whether deviations are prompt-driven or model-intrinsic.
3. Preprocessing sensitivity: evaluate how different normalization/tokenization rules affect Benford and Zipf statistics (e.g., removing currency symbols, expanding abbreviations).
4. Report & publish: freeze the canonical dataset and document preprocessing choices in a Methods appendix for reproducibility.

## 6. Deliverables and artifacts

- Canonical dataset: `sample_data/combined_outputs.jsonl`
- Summary CSV: `outputs/topic_comparison.csv` (observed digits obs_1..obs_9, expected counts, chi-square, p-value)
- Summary plots: `outputs/summary/chi2_heatmap.png`, `outputs/summary/benford_by_topic_combined.png`
- Scripts: `scripts/consolidate.py`, `scripts/generate_summary_plots.py`, `llm_verification/analyzer_benford.py`, `llm_verification/analyzer_zipf.py`

## 7. Reproducibility

- All analysis scripts operate on JSONL input and are deterministic given the same preprocessing parameters. Archived intermediate files are stored under `archive/` with timestamps for traceability.

---

Prepared: September 22, 2025
