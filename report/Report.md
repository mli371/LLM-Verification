# LLM Verification — Professor-facing report (draft)

This document is a concise, self-contained report intended for a short meeting or presentation with a supervisor/professor. It summarizes objectives, methods, key findings, and suggested next steps. You can use this as talking points or convert it to a PDF/slide.

## 1. Executive summary

- Goal: evaluate whether outputs from different LLMs (and prompt types) produce numeric/textual distributions consistent with expected empirical laws (Benford for numbers, Zipf for word frequencies). This helps detect generation artifacts, reporting anomalies, or systematic biases.
- Status: data collection and consolidation completed into `sample_data/combined_outputs.jsonl`. Summary analyses (Benford chi-square per topic/model and Zipf slope/R²) produced and visualized.

## 2. Methods (short)

- Collection: prompts organized by topic were used to generate multiple responses per model; all outputs recorded as JSONL with metadata (prompt id, model, timestamp).
- Preprocessing: responses were parsed for numbers and plain text; numeric tokens were normalized and leading digits extracted for Benford counts.
- Analysis: for each (topic, model) pair we computed counts of leading digits 1..9, expected Benford proportions, chi-square statistic and p-value (when available). For text we computed word-frequency distributions and estimated Zipf slope and R².
- Visualization: heatmaps of chi-square by topic/model and composite Benford plots per topic are available in `outputs/summary/`.

## 3. Key results (one-paragraph each)

- Benford checks: most human-like outputs (long numeric series or financial-like prompts) show reasonable agreement with Benford expectations; some model/topic pairs show elevated chi-square values indicating deviation. See `outputs/topic_comparison.csv` for per-pair statistics and `outputs/summary/chi2_heatmap.png` for a quick overview.
- Zipf checks: textual outputs generally follow a heavy-tailed distribution; Zipf slope estimates and R² indicate reasonable alignment for narrative/long-form prompts, while short structured prompts (tables, receipts) produce deviations expected from constrained vocabulary.

## 4. Important files and figures to review

- `sample_data/combined_outputs.jsonl` — canonical dataset used in analyses.
- `outputs/topic_comparison.csv` — per-topic/model Benford observed counts (obs_1..obs_9), expected counts, chi-square, p-value.
- `outputs/summary/chi2_heatmap.png` — visualization of chi-square (rows: topics, cols: models).
- `outputs/summary/benford_by_topic_combined.png` — combined Benford plots by topic.

## 5. Talking points for a short meeting (5–10 minutes)

- One-sentence goal.
- What we measured (Benford chi-square, Zipf slope/R²) and why it matters.
- Top 2–3 notable deviations: which topic/model pairs show significant Benford deviations and potential reasons (prompt style, numeric emphasis, tokenization quirks).
- Proposed next steps and experiments (see Section 6).

## 6. Suggested next steps (recommended order)

1. Validate top deviations by manually inspecting raw responses for the suspect (topic, model) pairs to understand failure modes (e.g., explicit enumerations, repeated tokens, formatting differences).
2. Run controlled prompt variants (A/B) for suspect prompts to localize whether deviation is prompt-driven or model-driven.
3. If publishing results, freeze the canonical dataset and append a short Methods appendix describing parsing choices and any normalization rules.
4. Optionally add a small slide deck with the two summary plots and the table of top deviations for easy sharing.

## 7. Reproducibility & notes for the professor

- The `scripts/` directory contains the consolidation and plotting scripts used to produce the CSVs and PNGs; `llm_verification/` contains analyzers and utilities.
- Archived legacy outputs are under `archive/` with timestamps in folder names — these are retained for reproducibility and can be restored if needed.

---

Prepared: September 22, 2025

(If you want, I can convert this to a PDF and create a one-slide summary in PPTX or PDF format.)
