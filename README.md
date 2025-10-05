# Hyrum Smith — Liberty Jail Journal (March–April 1839)
**A critical digital edition edited by Mark Phillips**

> This project preserves and presents the words of **Hyrum Smith** written during confinement in **Liberty Jail, Missouri** (late 1838–April 1839).  
> Each daily entry includes a **faithful (diplomatic) transcription**, a **modernized reading**, and light **annotations**, paired with the verified manuscript image.

See **[TOC.md](TOC.md)** for the chronological table of contents, or open any file in `transcripts/` to begin reading.

## How to contribute (images + transcripts)

This repository includes helper scripts to prepare images and validate transcript/metadata consistency.

- Create a Python virtual environment (optional but recommended) and install dependencies from `requirements.txt`.
- Process manuscript images (crop/deskew/enhance) into `images/processed/`.
- Validate transcripts, images, and metadata before committing.

### Working image reference (edited pages)

To make transcription easier, transcripts can include a `image_working_ref` in frontmatter that points to a readable, conservatively cropped image in `images/processed_safe_crop/`. This keeps `image_ref` pointing to the original provenance image while providing a high-contrast working view for editors.

- `image_ref`: Original manuscript image (provenance)
- `image_processed_ref`: Enhanced full-page image (no crop)
- `image_working_ref`: Enhanced, safe-cropped image for on-screen transcription

You can batch-add the working reference to all transcripts with:

```bash
python3 scripts/add_working_ref.py
```

### Image processing

Enhance all images with contrast equalization and denoising:

```bash
python3 scripts/process_images.py --all --crop --deskew --clahe --denoise --sharpen
```

Outputs go to `images/processed/` with the same filenames. You can point transcript `image_ref` to processed images if desired (retain originals in `images/`).

### OCR assist (optional)

Generate per-line crops to aid manual transcription, with optional OCR stubs if you have Tesseract installed:

```bash
python3 scripts/ocr_assist.py 1839-04-05 --ocr
```

Line crops and any OCR text files are saved under `images/lines/YYYY-MM-DD/`.

### Repository validation

Run consistency checks across transcripts, images, TOC, and metadata:

```bash
python3 scripts/validate_repository.py
```

The validator checks:

- Filenames vs. `date` in frontmatter
- Required frontmatter fields (`title`, `date`, `location`, `image_ref`, `provenance`, `editor`)
- Presence of both transcription sections
- Existence of the referenced image
- `metadata/date_mapping.json` contains the date key
- `TOC.md` includes links for each date

If issues are reported, fix them in the indicated file(s) and re-run.
