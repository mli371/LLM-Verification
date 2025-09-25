"""Consolidate JSONL outputs and prompts, assign topics using prompts_meta.json,
and compute a lightweight per-topic Benford summary CSV.

Usage:
  PYTHONPATH=. python scripts/consolidate.py

Produces:
  - sample_data/combined_outputs.jsonl
  - prompts/consolidated_prompts_by_topic.txt
  - outputs/topic_comparison.csv

This script is conservative: it backs up existing combined file if present, and
avoids touching backups (files with .bak in name).
"""
from __future__ import annotations
import json
import os
import re
from pathlib import Path
from collections import defaultdict, Counter
import math

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_DIR = ROOT / "sample_data"
PROMPTS_GLOB = ROOT.glob("prompts*.txt")
PROMPTS_META = ROOT / "prompts_meta.json"
OUTPUT_COMBINED = SAMPLE_DIR / "combined_outputs.jsonl"
CONSOLIDATED_PROMPTS = ROOT / "prompts" / "consolidated_prompts_by_topic.txt"
OUTPUT_CSV = ROOT / "outputs" / "topic_comparison.csv"

BENFORD_EXPECTED = {d: math.log10(1 + 1.0 / d) for d in range(1, 10)}


def load_meta_rules(meta_path: Path):
    rules = []
    if not meta_path.exists():
        return rules
    data = json.loads(meta_path.read_text())
    for entry in data:
        pattern = entry.get("pattern")
        typ = entry.get("type")
        regex = bool(entry.get("regex"))
        flags = entry.get("flags", "")
        compiled = None
        if regex:
            f = 0
            if "i" in flags.lower():
                f |= re.IGNORECASE
            try:
                compiled = re.compile(pattern, flags=f)
            except re.error:
                compiled = None
        rules.append({"pattern": pattern, "type": typ, "regex": regex, "compiled": compiled})
    return rules


def detect_topic(prompt_text: str, rules):
    if not prompt_text:
        return "unknown"
    for r in rules:
        if r["regex"] and r["compiled"] is not None:
            if r["compiled"].search(prompt_text):
                return r["type"]
        else:
            # non-regex: use case-insensitive substring match
            if r["pattern"].lower() in prompt_text.lower():
                return r["type"]
    return "other"


def list_jsonl_files(sample_dir: Path):
    files = []
    # search recursively to include files in subdirectories (e.g., by_topic)
    for p in sample_dir.rglob("*.jsonl"):
        if ".bak" in p.name or p.name == OUTPUT_COMBINED.name:
            continue
        # skip files inside tests/fixtures if any
        files.append(p)
    return sorted(files)


NUM_RE = re.compile(r"[+-]?\$?\(?\d[\d,\.eE]*")


def extract_numbers(text: str):
    if not text:
        return []
    matches = NUM_RE.findall(text)
    nums = []
    for m in matches:
        s = m
        # strip currency symbols and parentheses
        s = s.replace("$", "")
        s = s.replace("(", "-") if s.startswith("(") and s.endswith(")") else s
        s = s.replace(")", "")
        s = s.replace(",", "")
        try:
            val = float(s)
            nums.append(val)
        except Exception:
            # try to parse scientific or ignore
            try:
                nums.append(float(s))
            except Exception:
                continue
    return nums


def leading_digit(n: float):
    n = abs(n)
    if n == 0 or math.isnan(n) or math.isinf(n):
        return None
    # normalize to remove decimals and exponents
    # convert to string w/o scientific notation
    s = f"{n:.15g}"
    s = s.lstrip('0').lstrip('.')
    for ch in s:
        if ch.isdigit() and ch != '0':
            return int(ch)
    # fallback
    try:
        while n >= 10:
            n /= 10.0
        while n < 1 and n > 0:
            n *= 10.0
        d = int(n)
        return d if d >= 1 else None
    except Exception:
        return None


def compute_benford_stats(digits_counter: Counter):
    total = sum(digits_counter.get(d, 0) for d in range(1, 10))
    if total == 0:
        return {"n": 0, "chi2": None, "p": None, "obs": {}}
    obs = [digits_counter.get(d, 0) for d in range(1, 10)]
    exp = [BENFORD_EXPECTED[d] * total for d in range(1, 10)]
    chi2 = sum((o - e) ** 2 / e if e > 0 else 0.0 for o, e in zip(obs, exp))
    # try to compute p using scipy if available
    p = None
    try:
        import math
        try:
            from scipy.stats import chi2 as chi2dist
            p = 1.0 - chi2dist.cdf(chi2, df=8)
        except Exception:
            p = None
    except Exception:
        p = None
    return {"n": total, "chi2": chi2, "p": p, "obs": {d: digits_counter.get(d, 0) for d in range(1, 10)}}


def main():
    rules = load_meta_rules(PROMPTS_META)
    jsonl_files = list_jsonl_files(SAMPLE_DIR)
    print("Found JSONL files:", jsonl_files)

    # backup existing combined
    if OUTPUT_COMBINED.exists():
        bak = OUTPUT_COMBINED.with_suffix(OUTPUT_COMBINED.suffix + ".bak")
        print("Backing up existing combined to", bak)
        OUTPUT_COMBINED.replace(bak)

    seen = set()
    combined_records = []
    for jf in jsonl_files:
        with jf.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                key = json.dumps(rec, sort_keys=True)
                if key in seen:
                    continue
                seen.add(key)
                prompt_text = rec.get("prompt") or rec.get("instruction") or ""
                topic = detect_topic(prompt_text, rules)
                rec["_topic"] = topic
                combined_records.append(rec)

    # write combined
    OUTPUT_COMBINED.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_COMBINED.open("w", encoding="utf-8") as outfh:
        for rec in combined_records:
            outfh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"Wrote {len(combined_records)} records to {OUTPUT_COMBINED}")

    # consolidate prompts files
    prompts_by_topic = defaultdict(list)
    # read prompts files in repo root
    for p in ROOT.glob("prompts*.txt"):
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        for ln in lines:
            t = detect_topic(ln, rules)
            prompts_by_topic[t].append((p.name, ln))

    # ensure prompts dir
    CONSOLIDATED_PROMPTS.parent.mkdir(parents=True, exist_ok=True)
    with CONSOLIDATED_PROMPTS.open("w", encoding="utf-8") as pf:
        for topic in sorted(prompts_by_topic.keys()):
            pf.write(f"## TOPIC: {topic}\n")
            for src, ln in prompts_by_topic[topic]:
                pf.write(f"# source: {src}\n{ln}\n\n")
    print(f"Wrote consolidated prompts to {CONSOLIDATED_PROMPTS}")

    # compute per-topic per-model benford summary
    stats = []
    # structure: stats[(topic, model)] -> digits counter & counts
    combo = defaultdict(Counter)
    texts_count = defaultdict(int)
    texts_by_pair = defaultdict(list)
    for rec in combined_records:
        topic = rec.get("_topic", "other")
        model = rec.get("model", "unknown")
        texts_count[(topic, model)] += 1
        # extract numbers from response
        resp = rec.get("response") or rec.get("output") or ""
        # store responses for later Zipf analysis
        texts_by_pair[(topic, model)].append(resp)
        nums = extract_numbers(resp)
        for n in nums:
            d = leading_digit(n)
            if d is not None and 1 <= d <= 9:
                combo[(topic, model)][d] += 1

    # prepare CSV
    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_CSV.open("w", encoding="utf-8") as csvf:
        hdr = ["topic", "model", "n_texts", "n_numbers", "chi2", "p", "obs_1", "obs_2", "obs_3", "obs_4", "obs_5", "obs_6", "obs_7", "obs_8", "obs_9", "zipf_slope", "zipf_r2", "zipf_types"]
        csvf.write("\t".join(hdr) + "\n")
        for (topic, model), counter in sorted(combo.items()):
            ben = compute_benford_stats(counter)
            n_texts = texts_count.get((topic, model), 0)
            n_numbers = ben["n"]
            chi2 = ben["chi2"]
            p = ben["p"]
            row = [topic, model, str(n_texts), str(n_numbers), str(chi2) if chi2 is not None else "", str(p) if p is not None else ""]
            row += [str(ben["obs"].get(d, 0)) for d in range(1, 10)]
            # compute zipf stats for this (topic, model) if possible
            zipf_slope = ""
            zipf_r2 = ""
            zipf_types = ""
            try:
                from llm_verification.visualize import zipf_stats_for_texts
                texts = texts_by_pair.get((topic, model), [])
                stats_z = zipf_stats_for_texts(texts)
                if stats_z:
                    zipf_slope = str(stats_z.get('slope'))
                    zipf_r2 = str(stats_z.get('r2'))
                    zipf_types = str(stats_z.get('n_types'))
            except Exception:
                # if dependencies missing or any error, leave zipf fields empty
                pass

            row += [zipf_slope, zipf_r2, zipf_types]
            csvf.write("\t".join(row) + "\n")
    print(f"Wrote topic comparison CSV to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
