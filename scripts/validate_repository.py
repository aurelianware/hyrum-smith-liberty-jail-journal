#!/usr/bin/env python3
"""
Validates repository consistency for the Hyrum Smith Liberty Jail Journal digital edition.
Checks:
- Transcript filename/date frontmatter consistency
- Required YAML frontmatter fields present
- Transcript sections for Diplomatic and Modernized present
- Image file exists and matches naming
- metadata/date_mapping.json contains matching key for each transcript date
- TOC.md contains an entry for each transcript date

Exit code 0 on success, non-zero if issues found. Prints a concise report.
"""
from __future__ import annotations
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
TRANSCRIPTS_DIR = REPO_ROOT / "transcripts"
IMAGES_DIR = REPO_ROOT / "images"
METADATA_DIR = REPO_ROOT / "metadata"
TOC_FILE = REPO_ROOT / "TOC.md"
DATE_MAP_FILE = METADATA_DIR / "date_mapping.json"

FRONTMATTER_REQUIRED = [
    "title",
    "date",
    "location",
    "image_ref",
    "provenance",
    "editor",
]

@dataclass
class Issue:
    kind: str
    path: Path
    message: str

    def __str__(self) -> str:
        return f"[{self.kind}] {self.path}: {self.message}"

DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], int]:
    """Parses simple YAML-like frontmatter delimited by lines with '---'. Returns (mapping, end_index)."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines[:20]):
        if line.strip() == "---":
            if start is None:
                start = i
            else:
                end = i
                break
    else:
        return {}, -1

    mapping: Dict[str, str] = {}
    for line in lines[start + 1 : end]:
        if not line.strip() or line.strip().startswith("#"):
            continue
        if ":" in line:
            key, val = line.split(":", 1)
            mapping[key.strip()] = val.strip().strip('"')
    return mapping, end


def has_sections(text: str) -> Tuple[bool, bool]:
    dip = re.search(r"^###\s+Faithful\s*\(Diplomatic\)\s*Transcription", text, re.M) is not None
    mod = re.search(r"^###\s+Modernized\s*\(Readable\)\s*Transcription", text, re.M) is not None
    return dip, mod


def load_toc_dates(path: Path) -> List[str]:
    dates: List[str] = []
    if not path.exists():
        return dates
    text = path.read_text(encoding="utf-8")
    # Expect lines like | Apr 05, 1839 | ... | [link](transcripts/1839-04-05.md) |
    for m in re.finditer(r"\(transcripts/(\d{4}-\d{2}-\d{2})\.md\)", text):
        dates.append(m.group(1))
    return dates


def main() -> int:
    issues: List[Issue] = []

    # Load metadata date map
    date_map: Dict[str, str] = {}
    if DATE_MAP_FILE.exists():
        try:
            date_map = json.loads(DATE_MAP_FILE.read_text(encoding="utf-8"))
        except Exception as e:
            issues.append(Issue("metadata", DATE_MAP_FILE, f"Invalid JSON: {e}"))

    toc_dates = set(load_toc_dates(TOC_FILE))

    for md in sorted(TRANSCRIPTS_DIR.glob("*.md")):
        fname_date = md.stem
        if not DATE_RE.match(fname_date):
            issues.append(Issue("filename", md, "Filename must be YYYY-MM-DD.md"))
            continue
        text = md.read_text(encoding="utf-8")
        fm, end_idx = parse_frontmatter(text)
        if end_idx < 0:
            issues.append(Issue("frontmatter", md, "Missing YAML frontmatter delimiter '---'"))
            continue
        # Required fields
        for key in FRONTMATTER_REQUIRED:
            if key not in fm or not fm[key]:
                issues.append(Issue("frontmatter", md, f"Missing required field: {key}"))
        # Date consistency
        if fm.get("date") != fname_date:
            issues.append(Issue("date", md, f"Frontmatter date {fm.get('date')} != filename {fname_date}"))
        # Image reference exists
        img_rel = fm.get("image_ref", "")
        if not img_rel.startswith("../images/"):
            issues.append(Issue("image_ref", md, f"image_ref should be '../images/{fname_date}.jpg' (found: {img_rel})"))
        else:
            img_path = (md.parent / img_rel).resolve()
            if not img_path.exists():
                issues.append(Issue("image", md, f"Missing image file: {img_rel}"))
        # Sections present
        dip, mod = has_sections(text)
        if not dip:
            issues.append(Issue("sections", md, "Missing 'Faithful (Diplomatic) Transcription' section"))
        if not mod:
            issues.append(Issue("sections", md, "Missing 'Modernized (Readable) Transcription' section"))
        # Metadata map contains date
        if fname_date not in date_map:
            issues.append(Issue("metadata", DATE_MAP_FILE, f"date_mapping.json missing key for {fname_date}"))
        # TOC contains date
        if fname_date not in toc_dates:
            issues.append(Issue("toc", TOC_FILE, f"TOC.md missing entry for {fname_date}"))

    if issues:
        print("Validation issues found:\n")
        for i in issues:
            print(str(i))
        print(f"\nTotal issues: {len(issues)}")
        return 1
    else:
        print("All checks passed.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
