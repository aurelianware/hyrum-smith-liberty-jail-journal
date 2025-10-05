#!/usr/bin/env python3
"""
Batch image processing pipeline for manuscript pages.

Operations (configurable via CLI flags):
- Auto-crop borders by edge detection
- Deskew (estimate rotation) and rotate to correct
- Contrast-limited adaptive histogram equalization (CLAHE) for readability
- Denoise (non-local means)
- Sharpen

Outputs to images/processed/YYYY-MM-DD.jpg by default (keeps original filenames).

Usage examples:
  ./scripts/process_images.py --all --clahe --denoise --sharpen
  ./scripts/process_images.py 1839-04-05 --crop --deskew --clahe
"""
from __future__ import annotations
import argparse
from pathlib import Path
import sys

try:
    import cv2  # type: ignore
    import numpy as np  # type: ignore
except Exception as e:
    print("OpenCV (cv2) and numpy are required. Install with: pip install opencv-python-headless numpy", file=sys.stderr)
    raise

REPO_ROOT = Path(__file__).resolve().parents[1]
IMAGES_DIR = REPO_ROOT / "images"
OUT_DIR = IMAGES_DIR / "processed"


def load_image(path: Path):
    return cv2.imread(str(path))


def save_image(path: Path, img):
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), img, [int(cv2.IMWRITE_JPEG_QUALITY), 95])


def auto_crop(img, pad_frac: float = 0.02, min_area_frac: float = 0.7):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 50, 150)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return img
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)
    # Add padding as fraction of the smaller side
    pad = int(min(w, h) * max(0.0, pad_frac))
    x = max(0, x - pad)
    y = max(0, y - pad)
    w = min(img.shape[1] - x, w + 2 * pad)
    h = min(img.shape[0] - y, h + 2 * pad)
    cropped = img[y : y + h, x : x + w]
    # Avoid over-cropping: require minimum area, otherwise keep original
    orig_area = img.shape[0] * img.shape[1]
    crop_area = h * w
    if orig_area <= 0:
        return img
    if crop_area / float(orig_area) < min_area_frac:
        return img
    return cropped


def estimate_deskew_angle(gray):
    # Use Hough transform on edges to estimate dominant angle
    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLines(edges, 1, np.pi / 180, threshold=200)
    if lines is None:
        return 0.0
    angles = []
    for rho_theta in lines[:50]:
        rho, theta = rho_theta[0]
        angle = (theta * 180 / np.pi) - 90
        # Normalize to [-45, 45]
        if angle > 45: angle -= 90
        if angle < -45: angle += 90
        angles.append(angle)
    if not angles:
        return 0.0
    return float(np.median(angles))


def deskew(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    angle = estimate_deskew_angle(gray)
    if abs(angle) < 0.3:
        return img
    h, w = gray.shape
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    rotated = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
    return rotated


def apply_clahe(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    limg = cv2.merge((cl, a, b))
    return cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)


def denoise(img):
    return cv2.fastNlMeansDenoisingColored(img, None, 3, 3, 7, 21)


def sharpen(img):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def process_one(in_path: Path, out_path: Path, args):
    img = load_image(in_path)
    if img is None:
        print(f"Failed to read {in_path}", file=sys.stderr)
        return False
    if args.crop:
        img = auto_crop(img, pad_frac=args.crop_pad, min_area_frac=args.min_area)
    if args.deskew:
        img = deskew(img)
    if args.clahe:
        img = apply_clahe(img)
    if args.denoise:
        img = denoise(img)
    if args.sharpen:
        img = sharpen(img)
    save_image(out_path, img)
    return True


def main():
    p = argparse.ArgumentParser(description="Process manuscript images")
    p.add_argument("dates", nargs="*", help="Specific YYYY-MM-DD dates to process. If omitted with --all, processes all images.")
    p.add_argument("--all", action="store_true", help="Process all images in images/")
    p.add_argument("--outdir", default=str(OUT_DIR), help="Output directory")
    p.add_argument("--crop", action="store_true")
    p.add_argument("--crop-pad", type=float, default=0.02, help="Padding fraction around detected crop (default 0.02)")
    p.add_argument("--min-area", type=float, default=0.7, help="Minimum crop area fraction relative to original (default 0.7)")
    p.add_argument("--deskew", action="store_true")
    p.add_argument("--clahe", action="store_true")
    p.add_argument("--denoise", action="store_true")
    p.add_argument("--sharpen", action="store_true")

    args = p.parse_args()
    outdir = Path(args.outdir)

    targets: list[Path] = []
    if args.all:
        targets = sorted(IMAGES_DIR.glob("*.jpg"))
    else:
        for d in args.dates:
            targets.append(IMAGES_DIR / f"{d}.jpg")

    if not targets:
        print("No targets selected. Provide dates or --all.")
        return 1

    ok = 0
    for t in targets:
        out = outdir / t.name
        if process_one(t, out, args):
            ok += 1
    print(f"Processed {ok}/{len(targets)} images to {outdir}")
    return 0 if ok == len(targets) else 2


if __name__ == "__main__":
    sys.exit(main())
