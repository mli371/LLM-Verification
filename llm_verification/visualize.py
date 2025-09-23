import os
from collections import Counter
from typing import List
import numpy as np
import matplotlib.pyplot as plt
from .analyzer_benford import extract_numbers_from_text, first_digits, benford_expected
from .analyzer_zipf import tokenize
from .utils import read_jsonl
from .analyzer_benford import benford_chi_squared
from collections import defaultdict


def plot_benford_from_texts(texts: List[str], out_path: str):
    nums = []
    for t in texts:
        nums.extend(extract_numbers_from_text(t))
    fd = first_digits(nums)
    counts = np.array([Counter(fd).get(d, 0) for d in range(1, 10)])
    total = counts.sum()
    expected = benford_expected() * total

    fig, ax = plt.subplots()
    digits = list(range(1, 10))
    ax.bar(digits, counts, alpha=0.6, label='observed')
    ax.plot(digits, expected, marker='o', color='red', label='expected')
    ax.set_xticks(digits)
    ax.set_xlabel('First digit')
    ax.set_ylabel('Count')
    ax.set_title('Benford Analysis')
    ax.legend()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def plot_zipf_from_texts(texts: List[str], out_path: str):
    tokens = []
    for t in texts:
        tokens.extend(tokenize(t))
    counts = Counter(tokens)
    freqs = sorted(counts.values(), reverse=True)
    ranks = np.arange(1, len(freqs) + 1)

    fig, ax = plt.subplots()
    ax.scatter(np.log(ranks), np.log(freqs), s=8)
    # fit linear regression in log-log
    if len(ranks) >= 2:
        slope, intercept = np.polyfit(np.log(ranks), np.log(freqs), 1)
        fit = np.exp(intercept) * (ranks ** slope)
        ax.plot(np.log(ranks), np.log(fit), color='red')
    ax.set_xlabel('log(rank)')
    ax.set_ylabel('log(freq)')
    ax.set_title('Zipf Distribution')
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fig.savefig(out_path)
    plt.close(fig)


def load_responses_from_jsonl(path: str) -> List[str]:
    texts = []
    for rec in read_jsonl(path):
        r = rec.get('response')
        if r:
            texts.append(r)
    return texts


def plot_from_jsonl(path: str, out_dir: str = 'outputs'):
    texts = load_responses_from_jsonl(path)
    plot_benford_from_texts(texts, os.path.join(out_dir, 'benford.png'))
    plot_zipf_from_texts(texts, os.path.join(out_dir, 'zipf.png'))


def group_by_model(path: str):
    models = defaultdict(list)
    for rec in read_jsonl(path):
        model = rec.get('model', 'unknown')
        resp = rec.get('response')
        if resp:
            models[model].append(resp)
    return models


def benford_stats_for_texts(texts: List[str]):
    nums = []
    for t in texts:
        nums.extend(extract_numbers_from_text(t))
    fd = first_digits(nums)
    if not fd:
        return None
    chi2, p, counts, expected = benford_chi_squared(fd)
    return {'chi2': float(chi2), 'p': float(p), 'counts': counts.tolist(), 'expected': expected.tolist()}


def zipf_stats_for_texts(texts: List[str]):
    tokens = []
    for t in texts:
        tokens.extend(tokenize(t))
    counts = Counter(tokens)
    freqs = np.array(sorted(counts.values(), reverse=True))
    if len(freqs) < 2:
        return None
    ranks = np.arange(1, len(freqs) + 1).reshape(-1, 1)
    log_r = np.log(ranks).flatten()
    log_f = np.log(freqs)
    # fit linear model on log-log via numpy.polyfit
    slope, intercept = np.polyfit(log_r, log_f, 1)
    pred = slope * log_r + intercept
    # compute R^2 manually
    ss_res = np.sum((log_f - pred) ** 2)
    ss_tot = np.sum((log_f - np.mean(log_f)) ** 2)
    r2 = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0
    return {'slope': slope, 'r2': r2, 'n_types': int(len(freqs))}


def plot_per_model(path: str, out_dir: str = 'outputs'):
    models = group_by_model(path)
    os.makedirs(out_dir, exist_ok=True)
    combined = []
    zipf_overlay = plt.figure()
    ax_overlay = zipf_overlay.add_subplot(1,1,1)
    for model_name, texts in models.items():
        stats_b = benford_stats_for_texts(texts)
        stats_z = zipf_stats_for_texts(texts)
        # benford plot
        if stats_b:
            fig, ax = plt.subplots()
            digits = list(range(1, 10))
            counts = np.array(stats_b['counts'])
            expected = np.array(stats_b['expected'])
            ax.bar(digits, counts, alpha=0.6)
            ax.plot(digits, expected, marker='o', color='red')
            ax.set_title(
                f"Benford - {model_name} (p={stats_b['p']:.3g})"
            )
            fig.savefig(os.path.join(out_dir, f'benford_{model_name}.png'))
            plt.close(fig)
        # zipf plot
        if stats_z:
            fig, ax = plt.subplots()
            tokens = []
            for t in texts:
                tokens.extend(tokenize(t))
            freqs = sorted(Counter(tokens).values(), reverse=True)
            ranks = np.arange(1, len(freqs) + 1)
            ax.scatter(np.log(ranks), np.log(freqs), s=8)
            slope = stats_z['slope']
            # fit line for plotting
            coeffs = np.polyfit(np.log(ranks), np.log(freqs), 1)
            fit = np.exp(coeffs[1]) * (ranks ** coeffs[0])
            ax.plot(np.log(ranks), np.log(fit), color='red')
            ax.set_title(
                f"Zipf - {model_name} (slope={slope:.3g}, R2={stats_z['r2']:.3g})"
            )
            fig.savefig(os.path.join(out_dir, f'zipf_{model_name}.png'))
            plt.close(fig)
            # overlay
            ax_overlay.scatter(np.log(ranks), np.log(freqs), s=6, label=model_name)
    ax_overlay.set_title('Zipf overlay')
    ax_overlay.legend()
    zipf_overlay.savefig(os.path.join(out_dir, 'zipf_overlay.png'))
    plt.close(zipf_overlay)
    # return computed stats for possible further use
    return combined


def export_stats_csv(path: str, out_csv: str = 'outputs/stats_summary.csv'):
    """Compute per-model Benford and Zipf statistics and export to CSV."""
    import csv
    models = group_by_model(path)
    rows = []
    for model_name, texts in models.items():
        stats_b = benford_stats_for_texts(texts) or {}
        stats_z = zipf_stats_for_texts(texts) or {}
        rows.append({
            'model': model_name,
            'n_texts': len(texts),
            'benford_chi2': stats_b.get('chi2'),
            'benford_p': stats_b.get('p'),
            'zipf_slope': stats_z.get('slope'),
            'zipf_r2': stats_z.get('r2'),
            'zipf_types': stats_z.get('n_types'),
        })
    os.makedirs(os.path.dirname(out_csv), exist_ok=True)
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['model','n_texts','benford_chi2','benford_p','zipf_slope','zipf_r2','zipf_types'])
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    return out_csv
