#!/usr/bin/env python3
"""Analyze a real-benford JSONL file per-model and per-prompt-type.

This script accepts `--in` and `--out` and an optional `--plots` flag to save per-model
and per-type Benford bar plots under `outputs/`.
"""
import os
import re
import csv
import argparse
from collections import defaultdict
from typing import List

from llm_verification.utils import read_jsonl, split_response_to_numbers_and_text
from llm_verification.analyzer_benford import first_digits, benford_chi_squared
from llm_verification.visualize import plot_benford_from_texts


def classify_prompt_simple(prompt: str) -> str:
    p = prompt.lower()
    if re.search(r"\b(receipt|invoice|bill|total|subtotal)\b", p):
        return "financial_receipt"
    if re.search(r"\b(csv|comma separated|rows|columns|table|donation)\b", p):
        return "csv_table"
    if re.search(r"\b(sensor|temperature|humidity|reading|kwh)\b", p):
        return "sensor_logs"
    if re.search(r"\b(bank|transaction|statement|balance|debit|credit)\b", p):
        return "bank_statement"
    if re.search(r"\b(review|rating)\b", p):
        return "reviews"
    if re.search(r"\b(medical|lab|prescription|patient)\b", p):
        return "medical"
    if re.search(r"\b(narrative|story|paragraph|news)\b", p):
        return "narrative"
    return "other"


def analyze(path: str, out_csv: str, save_plots: bool = False):
    recs = list(read_jsonl(path))
    by_model = defaultdict(list)
    by_type = defaultdict(list)
    for r in recs:
        model = r.get("model", "unknown")
        prompt = r.get("prompt", "")
        resp = r.get("response")
        if not resp:
            continue
        by_model[model].append(resp)
        t = classify_prompt_simple(prompt)
        by_type[t].append(resp)

    rows = []
    # analyze models
    for model, texts in by_model.items():
        nums: List[str] = []
        for t in texts:
            n, _ = split_response_to_numbers_and_text(t)
            nums.extend(n)
        if nums:
            fd = first_digits(nums)
            chi2, p, counts, expected = benford_chi_squared(fd)
            rows.append({"group": "model", "name": model, "n_texts": len(texts), "n_numbers": len(nums), "chi2": chi2, "p": p})
        else:
            rows.append({"group": "model", "name": model, "n_texts": len(texts), "n_numbers": 0, "chi2": None, "p": None})

    # analyze types
    for typ, texts in by_type.items():
        nums: List[str] = []
        for t in texts:
            n, _ = split_response_to_numbers_and_text(t)
            nums.extend(n)
        if nums:
            fd = first_digits(nums)
            chi2, p, counts, expected = benford_chi_squared(fd)
            rows.append({"group": "type", "name": typ, "n_texts": len(texts), "n_numbers": len(nums), "chi2": chi2, "p": p})
        else:
            rows.append({"group": "type", "name": typ, "n_texts": len(texts), "n_numbers": 0, "chi2": None, "p": None})

    os.makedirs(os.path.dirname(out_csv) or '.', exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['group', 'name', 'n_texts', 'n_numbers', 'chi2', 'p'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print('Wrote', out_csv)

    # optionally save plots
    if save_plots:
        out_dir = os.path.dirname(out_csv) or 'outputs'
        os.makedirs(out_dir, exist_ok=True)
        # per-model
        for model, texts in by_model.items():
            out_path = os.path.join(out_dir, f'benford_expanded_model_{model}.png')
            try:
                plot_benford_from_texts(texts, out_path)
            except Exception:
                pass
        # per-type
        for typ, texts in by_type.items():
            out_path = os.path.join(out_dir, f'benford_expanded_type_{typ}.png')
            try:
                plot_benford_from_texts(texts, out_path)
            except Exception:
                pass

    # print concise summary
    print('Summary:')
    for r in rows:
        if r['chi2'] is None:
            print(f" - {r['group']}={r['name']}: n_texts={r['n_texts']} n_numbers={r['n_numbers']} (no numbers)")
        else:
            print(f" - {r['group']}={r['name']}: n_texts={r['n_texts']} n_numbers={r['n_numbers']} chi2={r['chi2']:.3f} p={r['p']:.3g}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--in', dest='infile', default='sample_data/real_benford_collect.jsonl', help='Input JSONL path')
    p.add_argument('--out', dest='outfile', default='outputs/real_benford_stats.csv', help='Output CSV path')
    p.add_argument('--plots', action='store_true', help='Save per-model and per-type Benford PNGs')
    args = p.parse_args()
    analyze(args.infile, args.outfile, save_plots=args.plots)


if __name__ == '__main__':
    main()
