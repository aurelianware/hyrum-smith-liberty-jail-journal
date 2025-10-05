#!/usr/bin/env python3
"""
Adds or updates image_processed_ref in transcript frontmatter to point to
../images/processed_full/YYYY-MM-DD.jpg for each transcript file.

Idempotent: re-runnable; preserves existing fields and ordering where possible.
"""
from __future__ import annotations
from pathlib import Path
import re

REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS = REPO_ROOT / "transcripts"

FRONTMATTER_DELIM = re.compile(r"^---\s*$", re.M)
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})$")


def process_file(path: Path) -> bool:
    date = path.stem
    if not DATE_RE.match(date):
        return False
    text = path.read_text(encoding="utf-8")
    # Find frontmatter block
    m = list(FRONTMATTER_DELIM.finditer(text))
    if len(m) < 2:
        return False
    start, end = m[0].end(), m[1].start()
    fm = text[start:end]
    lines = fm.splitlines()

    key = "image_processed_ref"
    target = f'"../images/processed_full/{date}.jpg"'

    found = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(key + ":"):
            new_lines.append(f"{key}: {target}")
            found = True
        else:
            new_lines.append(line)
    if not found:
        # Insert just after image_ref if present, else near the top
        inserted = False
        out = []
        for line in new_lines:
            out.append(line)
            if not inserted and line.strip().startswith("image_ref:"):
                out.append(f"{key}: {target}")
                inserted = True
        if not inserted:
            out.insert(0, f"{key}: {target}")
        new_lines = out

    new_fm = "\n".join(new_lines)
    # Ensure the frontmatter content ends with a newline so the closing '---' stays on its own line
    if not new_fm.endswith("\n"):
        new_fm += "\n"
    new_text = text[:start] + new_fm + text[end:]
    if new_text != text:
        path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main():
    changed = 0
    for md in sorted(TRANSCRIPTS.glob("*.md")):
        if process_file(md):
            changed += 1
    print(f"Updated {changed} transcript(s) with image_processed_ref")


if __name__ == "__main__":
    main()
