Summary outputs and archive

This folder contains consolidated summary plots and instructions.

Files produced by the cleanup step:
- `chi2_heatmap.png` - heatmap of Chi-square statistics (Benford) with topics as rows and models as columns.
- `benford_by_topic_combined.png` - small-multiples of observed leading-digit frequencies per topic compared to Benford's expected distribution.

Archived legacy images:
- All previous per-model and per-type PNG files were moved to `../archive/` to reduce clutter. If you need to restore them, run:

  mv ../archive/*.png .

or selectively copy files you need.

Notes:
- CSV/TSV files remain in `../` and contain the raw numeric/statistical outputs used to generate these summary plots.
- If you prefer permanent deletion of the archive, remove `../archive/` after verifying these summaries.
