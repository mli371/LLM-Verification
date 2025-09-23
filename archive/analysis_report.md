# LLM Verification — Analysis Report (by prompt type)

Date: 2025-09-21

## Summary

We analyzed collected model outputs (currently using gpt-3.5-turbo, gpt-4o, gpt-5-nano) by grouping responses into heuristic prompt types (narrative, financial_receipt, csv_table, sensor_logs, reviews, medical, other). For each group we computed Benford first-digit statistics and Zipf slope/R² on cleaned text (numbers removed).

Key findings:
- Narrative responses: Benford chi² p ≈ 0.96 (no rejection) — narrative-style data appears to better match Benford assumptions.
- csv_table and sensor_logs: strong rejection of Benford (p << 0.001) — expected because structured tables and sensor readings often have constrained ranges.
- financial_receipt: borderline (p ≈ 0.0266) — mixed behavior, suggests receipts sometimes approximate Benford but not always.

Zipf diagnostics:
- All groups exhibit Zipf-like frequency distributions with R² typically > 0.9 after cleaning (numbers removed), slopes in range ~ -0.7 to -1.2 depending on prompt type.

## Files produced
- `outputs/benford_by_prompt_type.csv` — per-type Benford & Zipf summary.
- `outputs/benford_{prompt_type}.png` — per-type Benford bar charts.
- `outputs/benford.png`, `outputs/zipf.png`, `outputs/zipf_overlay.png` — overall plots.

## Recommendations
1. Focus further data collection on `narrative` and `financial_receipt` prompt types — these are most likely to produce Benford-compatible numeric outputs. Use `csv_table`/`sensor_logs` as control groups.
2. For Zipf analysis, always use cleaned text (numbers/timestamps removed) to avoid inflating token diversity with structured numeric tokens.
3. Implement a refined prompt-type classifier (beyond keyword heuristics) or manual tagging for production-quality grouping.
4. Run staged sampling per model (pilot → estimate tokens/costs → scale) to ensure budget control.

## Next steps taken
- Save this report.
- Plan improvements to prompt classifier and prompt set, and produce a staged sampling plan (next tasks).
