import re
import math
from collections import Counter
from typing import List, Tuple
import numpy as np
from scipy.stats import chisquare

DIGIT_RE = re.compile(r"(?<!\d)(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?!\d)")


def extract_numbers_from_text(s: str) -> List[str]:
    return DIGIT_RE.findall(s)


def first_digits(numbers: List[str]) -> List[int]:
    out = []
    for n in numbers:
        n2 = n.replace(',', '')
        if n2.startswith('0') and '.' in n2:
            # leading zero decimal like 0.023 -> first non-zero digit
            s = n2.lstrip('0.')
            if s:
                out.append(int(s[0]))
        else:
            # integer or non-leading-zero decimal
            s = n2.lstrip('0')
            if s:
                out.append(int(s[0]))
    return out


def benford_expected() -> np.ndarray:
    return np.array([math.log10(1 + 1 / d) for d in range(1, 10)])


def benford_chi_squared(first_digits_list: List[int]) -> Tuple[float, float, np.ndarray, np.ndarray]:
    counts = np.array([
        Counter(first_digits_list).get(d, 0) for d in range(1, 10)
    ])
    total = counts.sum()
    if total == 0:
        raise ValueError('No digits to analyze')
    expected_prop = benford_expected()
    expected = expected_prop * total
    chi2, p = chisquare(counts, f_exp=expected)
    return chi2, p, counts, expected


if __name__ == '__main__':
    import sys
    from .utils import read_jsonl
    path = sys.argv[1]
    all_texts = []
    for rec in read_jsonl(path):
        # expect each record to have a 'response' field
        r = rec.get('response')
        if r:
            all_texts.append(r)
    nums = []
    for t in all_texts:
        nums.extend(extract_numbers_from_text(t))
    fd = first_digits(nums)
    chi2, p, counts, expected = benford_chi_squared(fd)
    print('chi2=', chi2, 'p=', p)
    print('counts=', counts)
    print('expected=', expected)
