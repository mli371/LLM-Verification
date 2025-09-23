#!/usr/bin/env python3
"""
Merge all files under archive/ into a single timestamped directory, deduplicate by content (SHA-256),
and avoid overwriting by renaming conflicts. Does not run git; file system operations only.

Usage: python scripts/merge_archives.py
"""
import hashlib
import shutil
from pathlib import Path
import sys
from datetime import datetime

ROOT = Path('archive')
if not ROOT.exists():
    print('No archive/ directory found.')
    sys.exit(1)

ts = datetime.utcnow().strftime('archive_merged_%Y%m%d_%H%M%S_utc')
TARGET = ROOT / ts
TARGET.mkdir(parents=True, exist_ok=True)

hash_map = {}  # sha256 -> target_path
moved = 0
skipped_dup = 0
renamed = 0

# Walk tree and collect files to move (skip the TARGET dir itself)
all_files = [p for p in ROOT.rglob('*') if p.is_file() and TARGET not in p.parents]

for p in all_files:
    try:
        # compute hash
        h = hashlib.sha256()
        with p.open('rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                h.update(chunk)
        digest = h.hexdigest()
        if digest in hash_map:
            # duplicate by content: remove original file
            print(f'DUPLICATE: {p} (same as {hash_map[digest]}) -- removing original')
            p.unlink()
            skipped_dup += 1
            continue
        # not seen: determine target name
        target_name = p.name
        dest = TARGET / target_name
        # if filename exists but content differs (shouldn't happen because we check digest map), rename
        suffix = 1
        while dest.exists():
            # check if same content (unlikely since digest not in map); if different, rename
            # compute existing file digest
            eh = hashlib.sha256()
            with dest.open('rb') as ef:
                for chunk in iter(lambda: ef.read(8192), b''):
                    eh.update(chunk)
            if eh.hexdigest() == digest:
                # same content as existing dest
                print(f'FOUND EQUIVALENT TARGET: {p} == {dest} -- removing original')
                p.unlink()
                skipped_dup += 1
                break
            # else pick a new name
            dest = TARGET / f"{p.stem}_dup{suffix}{p.suffix}"
            suffix += 1
        else:
            # move file
            shutil.move(str(p), str(dest))
            hash_map[digest] = dest
            moved += 1
    except Exception as e:
        print(f'ERROR processing {p}: {e}')

# cleanup: remove empty dirs under archive (except TARGET)
for d in sorted(ROOT.iterdir(), reverse=True):
    try:
        if d == TARGET:
            continue
        if d.is_dir() and not any(d.iterdir()):
            d.rmdir()
    except Exception:
        pass

print('\nDone.')
print(f'Moved: {moved}, Duplicates removed: {skipped_dup}, Renamed conflicts: {renamed}')
print(f'Merged files are in: {TARGET}')
print('Sample listing:')
for i, f in enumerate(sorted(TARGET.iterdir())):
    if i >= 200:
        break
    print(' -', f.name)
