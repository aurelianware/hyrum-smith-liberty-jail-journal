#!/usr/bin/env python3
"""
Normalize transcript YAML frontmatter:
- Ensure two proper '---' delimiter lines enclose frontmatter
- If closing delimiter is missing or stuck to a comment line (e.g., '...readability.---'), split it
- If no closing delimiter found, insert one before the first section header (### Faithful ...)

Safe and idempotent.
"""
from __future__ import annotations
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[1]
TRANS = REPO / "transcripts"

DELIM_LINE = re.compile(r"^---\s*$")
START_SECTION = re.compile(r"^###\s+Faithful\s*\(Diplomatic\)\s*Transcription\s*$")


def normalize_file(p: Path) -> bool:
    text = p.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Find the first standalone '---' as opening delimiter
    open_idx = next((i for i, ln in enumerate(lines) if ln.strip() == '---'), None)
    if open_idx is None:
        return False

    # Find Diplomatic section header
    dip_idx = next((i for i, ln in enumerate(lines) if START_SECTION.match(ln.strip())), None)
    if dip_idx is None:
        dip_idx = len(lines)

    # If a proper closing delimiter exists between open and dip header, nothing to do
    for i in range(open_idx + 1, min(dip_idx, len(lines))):
        if lines[i].strip() == '---':
            return False

    # Look for embedded '---' inside a line in the same region and split it
    for i in range(open_idx + 1, min(dip_idx, len(lines))):
        ln = lines[i]
        if '---' in ln:
            before, after = ln.split('---', 1)
            before = before.rstrip()
            after = after.lstrip()
            new_segment = []
            if before:
                new_segment.append(before)
            new_segment.append('---')
            if after:
                new_segment.append(after)
            lines[i:i+1] = new_segment
            new_text = "\n".join(lines)
            if not new_text.endswith("\n"):
                new_text += "\n"
            p.write_text(new_text, encoding="utf-8")
            return True

    # Otherwise, insert a clean closing delimiter line just before the Diplomatic header (or at end)
    insert_at = dip_idx
    lines.insert(insert_at, '---')
    new_text = "\n".join(lines)
    if not new_text.endswith("\n"):
        new_text += "\n"
    p.write_text(new_text, encoding="utf-8")
    return True


def main():
    fixed = 0
    for md in sorted(TRANS.glob('*.md')):
        if normalize_file(md):
            fixed += 1
    print(f"Normalized frontmatter in {fixed} file(s)")

if __name__ == '__main__':
    main()
