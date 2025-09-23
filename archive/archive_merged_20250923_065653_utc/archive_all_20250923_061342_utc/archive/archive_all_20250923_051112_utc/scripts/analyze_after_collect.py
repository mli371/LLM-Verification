#!/usr/bin/env python3
"""Analyze collected outputs by prompt type (heuristic) and export stats and plots.

Usage: python scripts/analyze_after_collect.py
"""
import os
import json
from typing import Optional, List, Dict
import re as _re
from collections import defaultdict
from llm_verification.utils import read_jsonl, split_response_to_numbers_and_text
from llm_verification.analyzer_benford import benford_chi_squared
from llm_verification.analyzer_zipf import tokenize
import csv


def load_meta_rules() -> List[Dict]:
    meta_path = os.path.join(os.getcwd(), 'prompts_meta.json')
    rules = []
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as mf:
                raw = json.load(mf)
                if isinstance(raw, dict):
                    for k, v in raw.items():
                        rules.append({'pattern': k, 'type': v, 'regex': False})
                elif isinstance(raw, list):
                    rules = raw
        except Exception:
            rules = []
    return rules





def classify_prompt(prompt: str, meta_overrides: Optional[dict] = None, meta_rules: Optional[list] = None) -> str:
    p = prompt.strip()
    # check exact overrides passed as dict
    if meta_overrides and p in meta_overrides:
        return meta_overrides[p]

    # apply meta rules loaded from prompts_meta.json (first match wins)
    rules_to_apply = meta_rules if meta_rules is not None else []
    for rule in rules_to_apply:
        try:
            if rule.get('regex'):
                flags = 0
                if rule.get('flags') == 'i':
                    flags = _re.IGNORECASE
                if _re.search(rule['pattern'], p, flags=flags):
                    return rule['type']
            else:
                if p == rule.get('pattern'):
                    return rule['type']
        except Exception:
            continue

    # stronger heuristics with regex fallback
    if _re.search(r'\b(receipt|invoice|bill|grocery|restaurant|total|subtotal|tax)\b', p, flags=_re.IGNORECASE):
        return 'financial_receipt'
    if _re.search(r'\b(bank transaction|statement|transaction|balance|debit|credit)\b', p, flags=_re.IGNORECASE):
        return 'bank_statement'
    if _re.search(r'\b(sensor|iot|temperature|humidity|meter reading|kwh|mwh)\b', p, flags=_re.IGNORECASE):
        return 'sensor_logs'
    if _re.search(r'\b(csv|comma separated|rows|columns|table|product_id|sku|donation|donor)\b', p, flags=_re.IGNORECASE):
        return 'csv_table'
    if _re.search(r'\b(review|product review|star rating|helpful)\b', p, flags=_re.IGNORECASE):
        return 'reviews'
    if _re.search(r'\b(news|report|paragraph|itinerary|narrative|story|summary|travelogue|funding|valuation|series a|series b)\b', p, flags=_re.IGNORECASE):
        return 'narrative'
    if _re.search(r'\b(medical|lab|prescription|patient|test result)\b', p, flags=_re.IGNORECASE):
        return 'medical'
    # final fallback
    return 'other'


def analyze(path='sample_data/sample_outputs.jsonl', out_dir='outputs'):
    os.makedirs(out_dir, exist_ok=True)
    META_RULES = load_meta_rules()
    groups = defaultdict(list)  # prompt_type -> list of responses
    prompt_map = defaultdict(list)  # prompt_type -> list of prompts (for debugging)
    # load optional meta overrides file (exact prompt -> type)
    meta_rules = []
    meta_path = os.path.join(os.getcwd(), 'prompts_meta.json')
    if os.path.exists(meta_path):
        try:
            with open(meta_path, 'r', encoding='utf-8') as mf:
                raw = json.load(mf)
                # support two formats: old exact-map (dict) or new list-of-rules
                if isinstance(raw, dict):
                    # convert to list of exact-match rules
                    for k, v in raw.items():
                        meta_rules.append({'pattern': k, 'type': v, 'regex': False})
                elif isinstance(raw, list):
                    for entry in raw:
                        # entry: {pattern: ..., type: ..., regex: true/false, flags: 'i' }
                        meta_rules.append(entry)
        except Exception:
            meta_rules = []

    for rec in read_jsonl(path):
        prompt = rec.get('prompt','')
        resp = rec.get('response')
        if not resp:
            continue
        # apply overrides (first matching rule wins)
        applied = None
        for rule in meta_rules:
            try:
                if rule.get('regex'):
                    flags = 0
                    if rule.get('flags') == 'i':
                        flags = 2  # re.IGNORECASE
                    import re
                    if re.search(rule['pattern'], prompt, flags=flags):
                        applied = rule['type']
                        break
                else:
                    # exact match
                    if prompt == rule.get('pattern'):
                        applied = rule['type']
                        break
            except Exception:
                continue
        t = classify_prompt(prompt, None, meta_rules=META_RULES) if applied is None else applied
        groups[t].append(resp)
        prompt_map[t].append(prompt)

    # compute benford stats per group and export CSV
    rows = []
    for typ, texts in groups.items():
        # gather numbers
        nums = []
        for t in texts:
            nums_part, cleaned = split_response_to_numbers_and_text(t)
            nums.extend(nums_part)
        fd = []
        try:
            from llm_verification.analyzer_benford import first_digits
            fd = first_digits(nums)
        except Exception:
            fd = []
        if fd:
            chi2, p, counts, expected = benford_chi_squared(fd)
            ben_chi2 = float(chi2)
            ben_p = float(p)
        else:
            ben_chi2 = None
            ben_p = None

        # zipf on cleaned texts (remove numbers so zipf focuses on words)
        tokens = []
        for t in texts:
            nums_part, cleaned = split_response_to_numbers_and_text(t)
            tokens.extend(tokenize(cleaned))
        zipf_slope = None
        zipf_r2 = None
        try:
            from llm_verification.visualize import zipf_stats_for_texts
            z = zipf_stats_for_texts(texts)
            if z:
                zipf_slope = z.get('slope')
                zipf_r2 = z.get('r2')
        except Exception:
            pass

        rows.append({'prompt_type': typ, 'n_responses': len(texts), 'benford_chi2': ben_chi2, 'benford_p': ben_p, 'zipf_slope': zipf_slope, 'zipf_r2': zipf_r2})

        # optional: save a small benford plot per type
        try:
            from llm_verification.visualize import plot_benford_from_texts
            plot_benford_from_texts(texts, os.path.join(out_dir, f'benford_{typ}.png'))
        except Exception:
            pass

    csv_path = os.path.join(out_dir, 'benford_by_prompt_type.csv')
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['prompt_type','n_responses','benford_chi2','benford_p','zipf_slope','zipf_r2'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print('Wrote', csv_path)


if __name__ == '__main__':
    analyze()
