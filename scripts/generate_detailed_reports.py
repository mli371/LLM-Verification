#!/usr/bin/env python3
"""Generate detailed CSV reports and plots per-model and per-prompt-type.

Usage: PYTHONPATH=. python scripts/generate_detailed_reports.py
"""
import os
import csv
from collections import defaultdict
from llm_verification.visualize import (
    group_by_model,
    benford_stats_for_texts,
    zipf_stats_for_texts,
    plot_benford_from_texts,
    plot_zipf_from_texts,
)
from llm_verification.utils import read_jsonl, split_response_to_numbers_and_text


def group_by_prompt_type(path):
    groups = defaultdict(list)
    for rec in read_jsonl(path):
        p = rec.get('prompt','')
        r = rec.get('response')
        if not r:
            continue
        # simple heuristic grouping by prompt text keywords (reuse lightweight logic)
        # We'll bucket by first matched keyword
        key = 'other'
        lp = p.lower()
        if any(k in lp for k in ['receipt','invoice','bill','total','subtotal']):
            key = 'financial_receipt'
        elif any(k in lp for k in ['bank','transaction','statement','balance']):
            key = 'bank_statement'
        elif any(k in lp for k in ['csv','comma separated','rows','columns','table']):
            key = 'csv_table'
        elif any(k in lp for k in ['sensor','temperature','humidity','reading']):
            key = 'sensor_logs'
        elif any(k in lp for k in ['review','rating','product review']):
            key = 'reviews'
        elif any(k in lp for k in ['medical','lab','prescription','patient']):
            key = 'medical'
        elif any(k in lp for k in ['news','report','paragraph','story','narrative']):
            key = 'narrative'
        groups[key].append(r)
    return groups


def write_model_stats(path, out_csv='outputs/detailed_model_stats.csv'):
    models = group_by_model(path)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    rows = []
    for model, texts in models.items():
        b = benford_stats_for_texts(texts) or {}
        z = zipf_stats_for_texts(texts) or {}
        rows.append({
            'model': model,
            'n_texts': len(texts),
            'benford_chi2': b.get('chi2'),
            'benford_p': b.get('p'),
            'zipf_slope': z.get('slope'),
            'zipf_r2': z.get('r2'),
            'zipf_types': z.get('n_types')
        })
        # write per-model plots
        try:
            plot_benford_from_texts(texts, os.path.join('outputs', f'benford_model_{model}.png'))
        except Exception:
            pass
        try:
            plot_zipf_from_texts(texts, os.path.join('outputs', f'zipf_model_{model}.png'))
        except Exception:
            pass

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "model",
                "n_texts",
                "benford_chi2",
                "benford_p",
                "zipf_slope",
                "zipf_r2",
                "zipf_types",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return out_csv


def write_prompt_type_stats(path, out_csv='outputs/detailed_prompt_type_stats.csv'):
    groups = group_by_prompt_type(path)
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    rows = []
    for typ, texts in groups.items():
        # collect numbers and compute benford residuals
        nums = []
        for t in texts:
            n, cleaned = split_response_to_numbers_and_text(t)
            nums.extend(n)
        try:
            b = benford_stats_for_texts(texts) or {}
        except Exception:
            b = {}
        try:
            z = zipf_stats_for_texts(texts) or {}
        except Exception:
            z = {}
        rows.append({
            'prompt_type': typ,
            'n_responses': len(texts),
            'benford_chi2': b.get('chi2'),
            'benford_p': b.get('p'),
            'zipf_slope': z.get('slope'),
            'zipf_r2': z.get('r2'),
        })
        # plots
        try:
            plot_benford_from_texts(texts, os.path.join('outputs', f'benford_type_{typ}.png'))
        except Exception:
            pass
        try:
            plot_zipf_from_texts(texts, os.path.join('outputs', f'zipf_type_{typ}.png'))
        except Exception:
            pass

    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "prompt_type",
                "n_responses",
                "benford_chi2",
                "benford_p",
                "zipf_slope",
                "zipf_r2",
            ],
        )
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return out_csv


if __name__ == '__main__':
    data_path = 'sample_data/sample_outputs.jsonl'
    print('Writing model stats...')
    print(write_model_stats(data_path))
    print('Writing prompt-type stats...')
    print(write_prompt_type_stats(data_path))
