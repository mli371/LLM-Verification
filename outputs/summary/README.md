Summary outputs and archive

This folder contains consolidated summary plots and instructions.

Files produced by the cleanup step:
- `chi2_heatmap.png` - heatmap of Chi-square statistics (Benford) with topics as rows and models as columns.
- `benford_by_topic_combined.png` - small-multiples of observed leading-digit frequencies per topic compared to Benford's expected distribution.

Archived legacy images:
- All previous per-model and per-type PNG files were moved to `../../archive/` to reduce clutter. If you need to restore them, run:

  mv ../../archive/*.png .

or selectively copy files you need.

  Note about Zipf statistics and new CSV columns
  ------------------------------------------------

  - The consolidation step now computes per-topic and per-model Zipf statistics and writes three new columns into `outputs/topic_comparison.csv`:
    - `zipf_slope` — fitted slope of the log(rank)-vs-log(freq) linear fit (expected near -1 for Zipf-like text).
    - `zipf_r2` — R² of the log-log linear fit indicating fit quality.
    - `zipf_types` — number of unique token types used for the fit.

  - These fields will be populated only when a topic/model pair has enough textual variety (the code requires at least two frequency types to perform a fit). Rows with insufficient text will have empty Zipf fields. Use `visualize.plot_per_model(...)` to generate per-model Zipf PNGs directly from the consolidated JSONL if you need per-model plots regardless of CSV contents.

  If you'd like this behavior changed (for example, always computing Zipf from raw responses or lowering the minimum tokens threshold), open an issue or a PR describing the desired change.
