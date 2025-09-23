"""Generate two summary plots and save under outputs/summary:
- chi2 heatmap (topics x models)
- benford_by_topic_combined (subplots: observed vs expected leading-digit frequency per topic)

Reads: outputs/topic_comparison.csv
Writes: outputs/summary/chi2_heatmap.png, outputs/summary/benford_by_topic_combined.png
"""
from __future__ import annotations
import csv
from collections import defaultdict
from math import log10
from pathlib import Path
import os
ROOT = Path(__file__).resolve().parents[1]
IN = ROOT / 'outputs' / 'topic_comparison.csv'
OUT_DIR = ROOT / 'outputs' / 'summary'
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Read topic_comparison.csv
rows = []
with IN.open('r', encoding='utf-8') as f:
    reader = csv.DictReader(f, delimiter='\t')
    for r in reader:
        rows.append(r)

# collect topics and models
topics = sorted(set(r['topic'] for r in rows))
models = sorted(set(r['model'] for r in rows))

# prepare chi2 matrix
chi2 = {t: {m: None for m in models} for t in topics}
# prepare per-topic digit obs sums
per_topic_digits = {t: [0]*9 for t in topics}
per_topic_n_numbers = {t: 0 for t in topics}
for r in rows:
    t = r['topic']
    m = r['model']
    try:
        chi = float(r['chi2']) if r['chi2'] else None
    except:
        chi = None
    chi2[t][m] = chi
    # obs_1..obs_9 may exist
    for i in range(1,10):
        key = f'obs_{i}'
        if key in r and r[key] != '':
            try:
                per_topic_digits[t][i-1] += int(r[key])
            except:
                pass
    try:
        per_topic_n_numbers[t] += int(r.get('n_numbers') or 0)
    except:
        pass

# Create chi2 heatmap
try:
    import numpy as np
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(max(6, len(models)*1.2), max(6, len(topics)*0.6)))
    mat = np.zeros((len(topics), len(models)))
    mask = np.zeros_like(mat, dtype=bool)
    for i,t in enumerate(topics):
        for j,m in enumerate(models):
            v = chi2[t].get(m)
            if v is None:
                mat[i,j] = 0.0
                mask[i,j] = True
            else:
                mat[i,j] = v
    # log-scale for color mapping to handle large chi2 range
    import numpy.ma as ma
    mat_masked = ma.masked_array(mat, mask=mask)
    # use symmetric log scaling
    from matplotlib.colors import LogNorm
    # add small epsilon
    eps = 1e-8
    vmin = max(mat_masked.min(), eps)
    # to avoid zeros in min
    im = ax.imshow(mat_masked, aspect='auto', cmap='viridis', norm=LogNorm(vmin=vmin, vmax=max(mat_masked.max(), vmin)))
    ax.set_yticks(list(range(len(topics))))
    ax.set_yticklabels(topics)
    ax.set_xticks(list(range(len(models))))
    ax.set_xticklabels(models, rotation=45, ha='right')
    ax.set_title('Chi-square (Benford) heatmap by Topic (rows) and Model (cols)')
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label('chi2 (log scale)')
    plt.tight_layout()
    out_chi = OUT_DIR / 'chi2_heatmap.png'
    plt.savefig(out_chi, dpi=150)
    plt.close(fig)
    print('Wrote', out_chi)
except Exception as e:
    print('Failed to create chi2 heatmap:', e)

# Create benford per-topic subplots (observed freq vs expected)
try:
    import matplotlib.pyplot as plt
    import numpy as np
    BENFORD = [log10(1 + 1.0/d) for d in range(1,10)]
    n_topics = len(topics)
    ncols = 3
    nrows = (n_topics + ncols - 1)//ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols*5, nrows*3.5))
    axes = axes.flatten()
    for idx, t in enumerate(topics):
        ax = axes[idx]
        obs = per_topic_digits[t]
        total = sum(obs)
        if total > 0:
            obs_freq = [o/total for o in obs]
        else:
            obs_freq = [0]*9
        ax.bar(range(1,10), obs_freq, label='observed', alpha=0.7)
        ax.plot(range(1,10), BENFORD, color='C1', marker='o', linestyle='--', label='Benford expected')
        ax.set_xticks(range(1,10))
        ax.set_ylim(0, max(max(obs_freq)*1.2, max(BENFORD)*1.2))
        ax.set_title(f'{t} (n_numbers={per_topic_n_numbers.get(t,0)})')
        ax.legend()
    # hide leftover axes
    for j in range(len(topics), len(axes)):
        axes[j].axis('off')
    plt.suptitle('Observed leading-digit frequencies per topic (vs Benford)')
    plt.tight_layout(rect=[0,0,1,0.97])
    out_ben = OUT_DIR / 'benford_by_topic_combined.png'
    plt.savefig(out_ben, dpi=150)
    plt.close(fig)
    print('Wrote', out_ben)
except Exception as e:
    print('Failed to create benford combined plot:', e)

print('Done')
