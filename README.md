LLM Verification — Project scaffold

Overview

This repository contains a minimal scaffold to run LLM verification experiments focused on:
- Benford analysis for numeric outputs
- Zipf (word frequency) analysis for textual outputs

What's included

- `requirements.txt` — Python dependencies
- `prompts.txt` — example prompts to use when generating outputs
- `sample_data/sample_outputs.jsonl` — a tiny example of model outputs (JSONL)
- `llm_verification/collector.py` — helper to collect outputs (from JSONL or OpenAI API if configured)
- `llm_verification/analyzer_benford.py` — Benford analysis utilities
- `llm_verification/analyzer_zipf.py` — Zipf analysis utilities
- `llm_verification/utils.py` — small I/O helpers
- `tests/test_benford.py`, `tests/test_zipf.py` — minimal unit tests using pytest

Quick start (macOS / zsh)

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run tests:

```bash
pytest -q
```

3. To analyze the provided sample data:

```bash
python -m llm_verification.analyzer_benford sample_data/sample_outputs.jsonl
python -m llm_verification.analyzer_zipf sample_data/sample_outputs.jsonl
```

Notes

- The `collector` supports reading from a JSONL file (already included) and optionally calling OpenAI if you set `OPENAI_API_KEY` and install `openai`.
- The scripts are intentionally small and easy to extend (add more prompts, models, or output fields).

Batching and running large collections

- `--batch-size` splits the prompt list into batches of the given size and processes all batches by default. If you want to limit how many batches to process (for stepwise collection), use `--max-batches`.
- `--max-prompts` lets you stop after processing a fixed number of prompts in total; the runner will trim the final batch to not exceed this limit.

Examples:

Process only one batch of size 2 (useful for stepwise testing):

```bash
conda activate MSproject
python -m llm_verification.runner --prompts prompts_big.txt --out sample_data/sample_outputs.jsonl --models gpt-3.5-turbo,gpt-4o,gpt-5-nano --n-per-prompt 1 --workers 2 --batch-size 2 --max-batches 1
```

Process up to 100 prompts total, trimming the last batch if needed:

```bash
python -m llm_verification.runner --prompts prompts_big.txt --out sample_data/sample_outputs.jsonl --models gpt-3.5-turbo --n-per-prompt 1 --workers 4 --batch-size 10 --max-prompts 100
```

Model naming and costs

- The runner will pass the exact model string you provide to the API. Ensure the model identifier matches what your provider expects (examples: `gpt-3.5-turbo`, `gpt-4o`, `gpt-5-nano`). If the model name is incorrect or not available on your account, individual requests will fail and record an error in the output JSONL.
- Large-scale collection may incur significant token costs. Consider:
	- Doing a full collection on a lower-cost model (e.g., `gpt-3.5-turbo`) and sampling the collected prompts/responses for higher-cost models.
	- Running a short small-scale run first to estimate average tokens per request and cost.

If you'd like, the repository can be extended to estimate token usage or perform automatic downsampling to reduce costs.

Next steps

- Run the tests and the sample analysis. If you'd like, I can implement plotting utilities, add more comprehensive tests, or create a small notebook with visualizations.