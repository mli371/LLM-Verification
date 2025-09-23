#!/usr/bin/env python3
"""Preview which prompt_type each prompt file maps to using the classifier."""
from scripts.analyze_after_collect import classify_prompt


def preview(prompts_path):
    with open(prompts_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith('#')]
    for i, p in enumerate(lines, start=1):
        t = classify_prompt(p)
        print(f'{i:02d}: {t} -> {p}')


if __name__ == '__main__':
    print('Preview prompts_stage3.txt')
    preview('prompts_stage3.txt')
    print('\nPreview prompts_stage2.txt')
    preview('prompts_stage2.txt')
