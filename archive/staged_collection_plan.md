# Staged Collection Plan

Goal
- Collect balanced, cost-controlled samples for two prompt types: `narrative` and `financial_receipt` across three models: `gpt-3.5-turbo`, `gpt-4o`, `gpt-5-nano`.
- Produce enough samples per type/model to make Benford test meaningful (preferably >= 50 responses per (type, model)) and Zipf stats stable.

Overview
- Stage 0: Pilot (dry run + tiny real sample)
  - Purpose: validate prompt templates, collector reliability, and small budget sanity-check.
  - Per model: 5 prompts × 1 response = 5 responses
  - Total (3 models): 15 responses
  - Command (dry-run):

```bash
PYTHONPATH=. python llm_verification/runner.py --prompts prompts_big.txt --models gpt-3.5-turbo gpt-4o gpt-5-nano --n-per-prompt 1 --batch-size 1 --max-batches 5 --dry-run
```

  - Command (small real pilot): change `--dry-run` to real, and set `--max-batches 5`.

- Stage 1: Focused collection (targeted prompts)
  - For each prompt type (`narrative`, `financial_receipt`) pick 10 distinct prompt templates from `prompts_big.txt` that match the type (use `prompts_meta.json` overrides or manual selection).
  - Per (type, model): 10 prompts × 5 responses = 50 responses.
  - Models: `gpt-3.5-turbo`, `gpt-4o`, `gpt-5-nano` → 3 models × 2 types × 50 = 300 responses total.
  - Suggested runner settings: `--n-per-prompt 5 --batch-size 5 --workers 5 --max-batches 10` (tune to keep concurrency moderate and not burst quota).
  - Example command (one model):

```bash
PYTHONPATH=. python llm_verification/runner.py \
  --prompts prompts_big.txt \
  --models gpt-5-nano \
  --n-per-prompt 5 \
  --batch-size 5 \
  --max-batches 10 \
  --workers 5 \
  --out sample_data/sample_outputs.jsonl
```

- Stage 2: Optional expansion (if Stage 1 shows variance and more data needed)
  - Increase `n-per-prompt` from 5 to 10 for weaker types, or expand to more prompts per type.

Cost estimates (very approximate)
- Assume average response tokens per prompt: 300 tokens output + 50 tokens prompt = 350 tokens. Pricing varies by model — replace with your exact pricing.
  - gpt-3.5-turbo (example): $0.0004 per 1K tokens → 0.0004×0.35 = $0.00014 per request → 100 requests ≈ $0.014
  - gpt-4o (example): $0.003 per 1K tokens → 0.003×0.35 = $0.00105 per request → 100 requests ≈ $0.105
  - gpt-5-nano (example): $0.006 per 1K tokens → 0.006×0.35 = $0.0021 per request → 100 requests ≈ $0.21

- For Stage 1 (300 requests) rough cost by model mix:
  - If evenly split across three models: ~100 requests/model → combine estimates above.
  - Total approximate cost (very rough): $0.014 + $0.105 + $0.21 ≈ $0.329 for 100 requests across three models; scale by 3 → ≈ $1.0 for 300 requests. (This is illustrative; check real model pricing and average token lengths.)

Operational notes
- Use `--dry-run` first to ensure prompts selected are the intended ones.
- Back up `sample_data/sample_outputs.jsonl` before any large append operations (the runner appends by default). Example:

```bash
cp sample_data/sample_outputs.jsonl sample_data/sample_outputs.jsonl.bak
```

- If you want model-specific outputs in separate files, run the runner per-model and supply different `--out` arguments.

Safety & rate-limits
- Keep `--workers` small (2–8) to avoid hitting request-rate limitations.
- Consider adding a small delay inside the runner between batches if you hit rate limit errors.

Next steps
- If you approve, I will (1) prepare a curated list of 10 `narrative` and 10 `financial_receipt` prompts (or mark prompts in `prompts_big.txt` with `prompts_meta.json` entries), (2) run Stage 0 pilot (dry-run + small real run), then run Stage 1.

```text
To proceed: reply 'approve' to run the pilot, or 'edit prompts' to curate the prompt list first.
```
