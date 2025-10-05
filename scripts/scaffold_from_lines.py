#!/usr/bin/env python3
"""
Scaffold Diplomatic transcription from line crops by placing one image-per-line
as markdown image references into the Diplomatic section for manual typing.
This avoids relying on OCR for cursive while keeping line boundaries.

Usage:
  ./scripts/scaffold_from_lines.py 1839-03-30

Effect:
- Inserts a skeletal structure in transcripts/DATE.md Diplomatic section:
  [Line 001] ![](../images/lines/DATE/line_001.jpg)
  (Transcribe here)

Idempotent: will replace previously scaffolded block (between markers) to update order if needed.
"""
from __future__ import annotations
from pathlib import Path
import re
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS = REPO_ROOT / "transcripts"
LINES_DIR = REPO_ROOT / "images" / "lines"

START_MARK = "<!-- SCAFFOLD_START -->"
END_MARK = "<!-- SCAFFOLD_END -->"


def build_scaffold(date: str) -> str:
    lines = sorted((LINES_DIR / date).glob("line_*.jpg"))
    parts = [START_MARK]
    for p in lines:
        name = p.name.replace(".jpg", "")
        parts.append(f"[Line {name.split('_')[-1]}] ![](../images/lines/{date}/{p.name})\n(Transcribe)\n")
    parts.append(END_MARK)
    return "\n".join(parts)


def insert_scaffold(md_path: Path, scaffold: str) -> bool:
    text = md_path.read_text(encoding="utf-8")
    # Locate Diplomatic section header
    m = re.search(r"^###\s+Faithful\s*\(Diplomatic\)\s*Transcription\s*$", text, re.M)
    if not m:
        return False
    start = m.end()
    # Find next section or end
    n = re.search(r"^###\s+Modernized\s*\(Readable\)\s*Transcription\s*$", text, re.M)
    end = n.start() if n else len(text)
    body = text[start:end]

    # Replace existing scaffold block if present, else prepend to section body
    if START_MARK in body and END_MARK in body:
        new_body = re.sub(rf"{START_MARK}.*?{END_MARK}", scaffold, body, flags=re.S)
    else:
        new_body = "\n\n" + scaffold + "\n\n" + body

    new_text = text[:start] + new_body + text[end:]
    if new_text != text:
        md_path.write_text(new_text, encoding="utf-8")
        return True
    return False


def main():
    if len(sys.argv) != 2:
        print("Usage: scaffold_from_lines.py YYYY-MM-DD", file=sys.stderr)
        return 1
    date = sys.argv[1]
    md = TRANSCRIPTS / f"{date}.md"
    if not md.exists():
        print(f"Transcript not found: {md}", file=sys.stderr)
        return 1
    if not (LINES_DIR / date).exists():
        print(f"No line crops found: {LINES_DIR/date}", file=sys.stderr)
        return 1
    scaffold = build_scaffold(date)
    changed = insert_scaffold(md, scaffold)
    if changed:
        print(f"Inserted scaffold into {md}")
    else:
        print("No changes (already up-to-date)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
