#!/usr/bin/env python3
"""Compute per-(model,prompt_type) counts and print a plan of runner commands to reach 100 each for target types.

Usage: PYTHONPATH=. python scripts/compute_stage2_plan.py
"""
from collections import defaultdict
from llm_verification.utils import read_jsonl
from scripts.analyze_after_collect import classify_prompt

TARGET_TYPES = ["narrative", "financial_receipt"]
TARGET_PER_PAIR = 100

def classify_prompt_simple(prompt):
    p = prompt.lower()
    if any(k in p for k in ['receipt','invoice','bill','total','subtotal']):
        return 'financial_receipt'
    if any(k in p for k in ['news','report','paragraph','story','narrative']):
        return 'narrative'
    return 'other'

def main():
    path = 'sample_data/sample_outputs.jsonl'
    counts = defaultdict(lambda: defaultdict(int))  # model -> type -> count
    for rec in read_jsonl(path):
        model = rec.get('model','unknown')
        prompt = rec.get('prompt','')
        t = classify_prompt(prompt)
        counts[model][t] += 1

    print("Current counts per model and type:")
    for model, d in counts.items():
        print(model)
        for t in TARGET_TYPES:
            print(f'  {t}: {d.get(t,0)}')

    # plan: for each model and target type, compute needed additional samples
    commands = []
    for model, d in counts.items():
        for t in TARGET_TYPES:
            have = d.get(t,0)
            need = TARGET_PER_PAIR - have
            if need > 0:
                # determine prompts count we have for that type in prompts_big/prompts_stage1
                # For simplicity we'll reuse prompts_stage1.txt and run only prompts matching type by meta rules
                parts = [
                    "PYTHONPATH=. python -m llm_verification.runner",
                    "--prompts prompts_stage2.txt",
                    "--out sample_data/sample_outputs.jsonl",
                    f"--models {model}",
                    "--n-per-prompt 1",
                    "--batch-size 5",
                    f"--max-batches {max(1, (need+4)//5)}",
                    "--workers 3",
                ]
                cmd = " ".join(parts)
                commands.append({'model': model, 'type': t, 'have': have, 'need': need, 'cmd': cmd})

    print('\nStage2 commands (run sequentially):')
    for c in commands:
        print(f"# model={c['model']} type={c['type']} have={c['have']} need={c['need']}")
        print(c['cmd'])

if __name__ == '__main__':
    main()
