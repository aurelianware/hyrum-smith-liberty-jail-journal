#!/usr/bin/env python3
"""
OCR assist for cursive/handwritten pages. This provides a helper workflow:
- Generate high-contrast crops and line-segment previews for manual review
- Optionally run Tesseract (if installed) as a rough baseline (handwriting often poor)
- Save per-line images to images/lines/YYYY-MM-DD/ for fine-grained transcription

Note: For historical handwriting, human transcription is primary; OCR is advisory.
"""
from __future__ import annotations
import argparse
from pathlib import Path
import subprocess
import sys

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception as e:
    print("Requires OpenCV and numpy. Install with: pip install opencv-python-headless numpy", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = REPO_ROOT / "images"
LINES_DIR = IMAGES_DIR / "lines"
PROCESSED_FULL = IMAGES_DIR / "processed_full"
PROCESSED_SAFE = IMAGES_DIR / "processed_safe_crop"

def segment_lines(img, preview: bool = False):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Boost contrast for handwriting
    gray = cv2.equalizeHist(gray)
    # Adaptive threshold for non-uniform lighting
    thr = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 31, 12)
    # Remove small noise
    thr = cv2.medianBlur(thr, 3)
    # Connect characters into lines with horizontal dilation
    kx = max(25, img.shape[1] // 50)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kx, 3))
    dil = cv2.dilate(thr, kernel, iterations=1)
    # Find contours of line blobs
    contours, _ = cv2.findContours(dil, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    raw_boxes = [cv2.boundingRect(c) for c in contours]
    # Filter boxes by reasonable height/width
    H, W = img.shape[:2]
    min_h, max_h = max(12, H // 100), max(15, H // 12)
    min_w = W // 6
    boxes = [b for b in raw_boxes if (min_h <= b[3] <= max_h) and (b[2] >= min_w)]
    # Sort top-to-bottom
    boxes = sorted(boxes, key=lambda b: b[1])
    # Merge overlapping/adjacent in Y
    merged = []
    for x, y, w, h in boxes:
        if not merged:
            merged.append([x, y, w, h])
            continue
        px, py, pw, ph = merged[-1]
        if y <= py + int(ph * 0.6):
            nx = min(px, x)
            ny = min(py, y)
            nw = max(px + pw, x + w) - nx
            nh = max(py + ph, y + h) - ny
            merged[-1] = [nx, ny, nw, nh]
        else:
            merged.append([x, y, w, h])
    # Optional preview overlay
    overlay = None
    if preview:
        overlay = img.copy()
        for (x, y, w, h) in merged:
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), 2)
    return merged, overlay


def try_tesseract(img_path: Path) -> str:
    try:
        # macOS often has tesseract via brew
        out = subprocess.run(["tesseract", str(img_path), "stdout", "--oem", "1", "--psm", "7"],
                             check=False, capture_output=True, text=True)
        return out.stdout.strip()
    except FileNotFoundError:
        return ""


def pick_source(date: str, source: str) -> Path:
    if source == "processed_full":
        p = PROCESSED_FULL / f"{date}.jpg"
        if p.exists():
            return p
    if source == "processed_safe":
        p = PROCESSED_SAFE / f"{date}.jpg"
        if p.exists():
            return p
    return IMAGES_DIR / f"{date}.jpg"


def make_contact_sheet(outdir: Path, lines: list[Path], cols: int = 4, thumb_w: int = 600) -> None:
    if not lines:
        return
    imgs = [cv2.imread(str(p)) for p in lines]
    imgs = [i for i in imgs if i is not None]
    if not imgs:
        return
    # Resize maintaining aspect ratio
    thumbs = []
    for i in imgs:
        h, w = i.shape[:2]
        scale = thumb_w / float(w)
        th = int(h * scale)
        thumbs.append(cv2.resize(i, (thumb_w, th)))
    rows = (len(thumbs) + cols - 1) // cols
    row_imgs = []
    max_row_w = 0
    for r in range(rows):
        row = thumbs[r * cols : (r + 1) * cols]
        if not row:
            continue
        max_h = max(im.shape[0] for im in row)
        # Pad each image in the row to the same height
        padded = [cv2.copyMakeBorder(im, 0, max_h - im.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(255, 255, 255)) for im in row]
        row_img = cv2.hconcat(padded)
        row_imgs.append(row_img)
        if row_img.shape[1] > max_row_w:
            max_row_w = row_img.shape[1]
    # Pad each row image to the same width so vconcat works
    uniform_rows = []
    for row_img in row_imgs:
        pad_w = max_row_w - row_img.shape[1]
        if pad_w > 0:
            row_img = cv2.copyMakeBorder(row_img, 0, 0, 0, pad_w, cv2.BORDER_CONSTANT, value=(255, 255, 255))
        uniform_rows.append(row_img)
    sheet = cv2.vconcat(uniform_rows)
    cv2.imwrite(str(outdir / "_contact_sheet.jpg"), sheet, [int(cv2.IMWRITE_JPEG_QUALITY), 90])


def process_date(date: str, do_ocr: bool, source: str, clean: bool, preview: bool, contact_sheet: bool) -> int:
    in_path = pick_source(date, source)
    if not in_path.exists():
        print(f"Image not found: {in_path}", file=sys.stderr)
        return 1
    img = cv2.imread(str(in_path))
    if img is None:
        print(f"Failed to read image: {in_path}", file=sys.stderr)
        return 2
    boxes, overlay = segment_lines(img, preview=preview)
    outdir = LINES_DIR / date
    if clean and outdir.exists():
        for p in outdir.glob("*"):
            try:
                p.unlink()
            except IsADirectoryError:
                pass
    outdir.mkdir(parents=True, exist_ok=True)

    if preview and overlay is not None:
        cv2.imwrite(str(outdir / "_preview.jpg"), overlay, [int(cv2.IMWRITE_JPEG_QUALITY), 90])

    for i, (x, y, w, h) in enumerate(boxes, start=1):
        crop = img[y:y+h, x:x+w]
        # Enhance line crop for readability
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)
        crop = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        line_path = outdir / f"line_{i:03d}.jpg"
        cv2.imwrite(str(line_path), crop, [int(cv2.IMWRITE_JPEG_QUALITY), 95])
        if do_ocr:
            text = try_tesseract(line_path)
            if text:
                (outdir / f"line_{i:03d}.txt").write_text(text + "\n", encoding="utf-8")
    if contact_sheet:
        make_contact_sheet(outdir, sorted(outdir.glob('line_*.jpg')))
    print(f"{date}: Saved {len(boxes)} line crops to {outdir} (source={source})")
    return 0


def main():
    p = argparse.ArgumentParser(description="Segment lines and (optionally) run OCR per line")
    p.add_argument("dates", nargs="*", help="One or more YYYY-MM-DD dates to process")
    p.add_argument("--all", action="store_true", help="Process all images under images/")
    p.add_argument("--ocr", action="store_true", help="Attempt Tesseract OCR per line (advisory)")
    p.add_argument("--source", choices=["processed_full", "processed_safe", "original"], default="processed_full",
                   help="Which image set to segment (default processed_full)")
    p.add_argument("--clean", action="store_true", help="Remove existing line crops before writing new ones")
    p.add_argument("--preview", action="store_true", help="Write overlay preview with detected line boxes (_preview.jpg)")
    p.add_argument("--contact-sheet", action="store_true", help="Write a tiled contact sheet of line crops (_contact_sheet.jpg)")
    args = p.parse_args()

    targets: list[str] = []
    if args.all:
        src_dir = PROCESSED_FULL if args.source == 'processed_full' else (PROCESSED_SAFE if args.source == 'processed_safe' else IMAGES_DIR)
        for img in sorted(src_dir.glob("*.jpg")):
            targets.append(img.stem)
    else:
        targets = list(args.dates)

    if not targets:
        print("No targets provided. Pass dates or --all.")
        return 1

    failures = 0
    for d in targets:
        rc = process_date(d, args.ocr, args.source, args.clean, args.preview, args.contact_sheet)
        if rc != 0:
            failures += 1
    if failures:
        print(f"Completed with {failures} failures.")
        return 2
    print("All line crops generated successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
