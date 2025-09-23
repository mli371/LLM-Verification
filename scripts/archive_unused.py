"""Archive files not in a small whitelist into a timestamped archive directory.

Usage:
  # dry-run (lists candidates, does NOT move)
  PYTHONPATH=. python scripts/archive_unused.py --dry-run

  # interactive: lists candidates then ask to continue
  PYTHONPATH=. python scripts/archive_unused.py

  # non-interactive (auto move)
  PYTHONPATH=. python scripts/archive_unused.py --auto

Notes:
- Edit WHITELIST at top to change which files/dirs are kept.
- Script preserves relative paths under archive/archive_all_<ts>/ and writes meta.json.
"""
from __future__ import annotations

import argparse
import shutil
import os
import sys
import datetime
from pathlib import Path
from typing import List, Set

# === EDIT THIS WHITELIST to control what is kept (paths relative to repo root) ===
WHITELIST = {
    # keep core package
    "llm_verification",
    # keep main scripts we want to keep
    "scripts/consolidate.py",
    "scripts/generate_summary_plots.py",
    "scripts/archive_unused.py",
    "scripts/analyze_real_benford_collect.py",
    "scripts/compute_stage2_plan.py",
    # keep prompt folder and consolidated prompts
    "prompts",
    "prompts/consolidated_prompts_by_topic.txt",
    "prompts_benford_stage.txt",
    "prompts_benford_AB_A.txt",
    "prompts_benford_AB_B.txt",
    # keep consolidated sample data and per-topic exports
    "sample_data/combined_outputs.jsonl",
    "sample_data/by_topic",
    "sample_data/real_benford_collect_expanded.jsonl",
    "sample_data/real_benford_AB_A.jsonl",
    "sample_data/real_benford_AB_B.jsonl",
    # keep outputs summary files and CSVs
    "outputs/topic_comparison.csv",
    "outputs/topic_summary.tsv",
    "outputs/summary",
    "outputs/real_benford_expanded_stats.csv",
    # keep README, requirements etc.
    "README.md",
    "requirements.txt",
    ".gitignore",
    "tests",
}

# File/dir name patterns to ignore from archiving (hidden VCS, envs)
IGNORE_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache"}
IGNORE_EXT = {".bak", ".zip"}  # you can extend if needed

# === end of config ===

ROOT = Path(".").resolve()


def is_whitelisted(path: Path, whitelist: Set[str]) -> bool:
    rel = path.relative_to(ROOT)
    # Check direct path or prefix directory in whitelist
    for w in whitelist:
        wpath = Path(w)
        try:
            # if the whitelist item is a directory, allow files under it
            if wpath == rel or wpath in rel.parents:
                return True
        except Exception:
            pass
    return False


def collect_candidates(root: Path, whitelist: Set[str]) -> List[Path]:
    candidates = []
    for p in root.rglob("*"):
        if p == root:
            continue
        # skip ignored directories anywhere in the path
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        if p.is_dir():
            continue
        if p.suffix in IGNORE_EXT:
            continue
        if is_whitelisted(p, whitelist):
            continue
        candidates.append(p)
    return sorted(candidates)


def print_candidates(cands: List[Path], limit: int = 200) -> None:
    if not cands:
        print("No candidates found for archiving.")
        return
    print(f"Found {len(cands)} candidate files to archive. Sample:")
    for i, p in enumerate(cands[:limit], 1):
        print(f"{i:3d}. {p}")
    if len(cands) > limit:
        print(f"... and {len(cands)-limit} more.")


def archive_files(cands: List[Path], dst_root: Path) -> None:
    for p in cands:
        rel = p.relative_to(ROOT)
        dst = dst_root / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(p), str(dst))
    print(f"Moved {len(cands)} files to {dst_root}")


def main():
    parser = argparse.ArgumentParser(
        description="Archive non-whitelisted files into a timestamped archive directory."
    )
    parser.add_argument("--dry-run", action="store_true", help="List candidates but don't move.")
    parser.add_argument("--auto", action="store_true", help="Do not prompt, move files.")
    parser.add_argument("--whitelist-file", type=str, help="Optional file with additional whitelist paths (one per line).")
    args = parser.parse_args()

    whitelist = set(WHITELIST)
    if args.whitelist_file:
        wf = Path(args.whitelist_file)
        if wf.exists():
            for line in wf.read_text().splitlines():
                s = line.strip()
                if s and not s.startswith("#"):
                    whitelist.add(s)

    candidates = collect_candidates(ROOT, whitelist)
    print_candidates(candidates)

    if not candidates:
        return

    if args.dry_run:
        print("Dry-run: no files moved. Re-run without --dry-run to perform archive.")
        return

    if not args.auto:
        resp = input("Archive the above files? Type 'yes' to continue: ").strip().lower()
        if resp != "yes":
            print("Aborted by user.")
            return

    ts = datetime.datetime.utcnow().strftime("archive_all_%Y%m%d_%H%M%S_utc")
    archive_root = ROOT / "archive" / ts
    archive_root.mkdir(parents=True, exist_ok=True)
    archive_files(candidates, archive_root)
    # create a small metadata file
    meta = {
        "timestamp": ts,
        "moved_count": len(candidates),
        "archive_path": str(archive_root),
    }
    try:
        import json

        (archive_root / "meta.json").write_text(json.dumps(meta, indent=2))
    except Exception:
        pass
    print("Archive complete. Review files under:", archive_root)
    print("If you want to permanently delete them, remove that folder after review.")


if __name__ == "__main__":
    main()
