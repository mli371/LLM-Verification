import json
from typing import Iterator, Dict


def read_jsonl(path: str) -> Iterator[Dict]:
    """Read a JSONL file robustly.

    This function tolerates multiple JSON objects concatenated on the same line
    (e.g. "{}{}") and JSON objects split across multiple lines by buffering and
    using JSONDecoder.raw_decode.
    """
    decoder = json.JSONDecoder()
    with open(path, 'r', encoding='utf-8') as f:
        buffer = ''
        for line in f:
            if not line.strip():
                continue
            buffer += line
            buffer = buffer.lstrip()
            while buffer:
                try:
                    obj, idx = decoder.raw_decode(buffer)
                    yield obj
                    buffer = buffer[idx:]
                except json.JSONDecodeError:
                    # Need more data to decode a full JSON object
                    break
        # Attempt to decode any remaining buffer
        buffer = buffer.lstrip()
        while buffer:
            try:
                obj, idx = decoder.raw_decode(buffer)
                yield obj
                buffer = buffer[idx:]
            except json.JSONDecodeError:
                # Give up on incomplete trailing data
                break


def save_json(path: str, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def split_response_to_numbers_and_text(s: str):
    """Return (numbers_list, cleaned_text) where numbers_list are numeric substrings suitable for Benford
    and cleaned_text is the input with numbers/dates/serials removed for Zipf analysis.
    """
    import re
    import re
    if not s:
        return [], ''
    # regex for numbers (with optional leading sign and currency), scientific
    # capture group 'num' contains the numeric token possibly with sign/currency
    num_re = re.compile(r"(?<!\w)(?P<num>[-+]?\s*[$€£¥]?\s*(?:\d{1,3}(?:,\d{3})*|\d+)(?:\.\d+)?(?:[eE][+-]?\d+)?)")
    time_re = re.compile(r"\b\d{2}:\d{2}:\d{2}(?:\.\d+)?\b")
    # extract numbers
    numbers = num_re.findall(s)
    # iterate with spans so we can detect surrounding parentheses for negative values
    numbers = []
    for m in num_re.finditer(s):
        raw = m.group('num')
        start, end = m.span('num')
        # normalize: remove spaces and thousands separators
        norm = raw.replace(' ', '').replace(',', '')
        # strip common currency symbols from start
        norm = re.sub(r'^[\$€£¥]+', '', norm)
        # strip trailing percent
        norm = norm.rstrip('%')
        # detect parentheses around the numeric token in the original string
        has_paren_negative = False
        if start > 0 and end < len(s) and s[start - 1] == '(' and s[end] == ')':
            has_paren_negative = True
        try:
            val = float(norm)
            if has_paren_negative:
                val = -val
            numbers.append(val)
        except Exception:
            # fallback: try to remove non numeric chars and parse
            try:
                fallback = re.sub(r'[^0-9eE+\-\.]', '', norm)
                val = float(fallback)
                if has_paren_negative:
                    val = -val
                numbers.append(val)
            except Exception:
                continue

    # remove numbers and dates/times from text
    cleaned = num_re.sub(' ', s)
    cleaned = time_re.sub(' ', cleaned)
    # remove typical serial patterns like ABC-12345-678
    cleaned = re.sub(r"[A-Z]{2,}-\d[-A-Z0-9]+", ' ', cleaned)
    # normalize whitespace
    cleaned = re.sub(r"\s+", ' ', cleaned).strip()
    return numbers, cleaned
