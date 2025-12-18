import regex as re
from collections import Counter
from typing import List, Tuple
import numpy as np
from scipy import stats

WORD_RE = re.compile(r"[\p{L}']+", re.UNICODE)


def tokenize(s: str) -> List[str]:
    # lowercase and simple tokenization
    return [w.lower() for w in WORD_RE.findall(s)]


def zipf_stats(texts: List[str]) -> Tuple[List[int], List[int], float]:
    tokens = []
    for t in texts:
        tokens.extend(tokenize(t))
    counts = Counter(tokens)
    freqs = sorted(counts.values(), reverse=True)
    ranks = list(range(1, len(freqs)+1))
    # fit a power-law on log-log
    log_r = np.log(ranks)
    log_f = np.log(freqs)
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_r, log_f)
    return ranks, freqs, slope, r_value**2


if __name__ == '__main__':
    import sys
    from .utils import read_jsonl
    path = sys.argv[1]
    all_texts = []
    for rec in read_jsonl(path):
        r = rec.get('response')
        if r:
            all_texts.append(r)
    ranks, freqs, slope = zipf_stats(all_texts)
    print('slope=', slope)
    print('top 20 ranks/freqs=', list(zip(ranks[:20], freqs[:20])))
