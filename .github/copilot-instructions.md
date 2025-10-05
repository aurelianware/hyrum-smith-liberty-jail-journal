# Hyrum Smith Liberty Jail Journal — AI Instructions

## Project Overview
This is a **digital critical edition** of Hyrum Smith's writings from Liberty Jail (March–April 1839). The project preserves historical documents through dual-track transcription: faithful diplomatic versions and modernized readable versions.

## Architecture & File Structure

### Core Components
- **`transcripts/`** — Daily journal entries (YYYY-MM-DD.md format)
- **`images/`** — Manuscript page images (1:1 mapping with transcripts)
- **`metadata/`** — Structured data linking images to dates and scholarly metadata
- **`docs/`** — Editorial documentation and scholarly apparatus
- **`compiled/`** — Generated PDF outputs

### Critical Data Flow
1. Each date has three linked files: `transcripts/YYYY-MM-DD.md` + `images/YYYY-MM-DD.jpg` + entry in `metadata/date_mapping.json`
2. Transcript files contain both diplomatic and modernized versions of the same source text
3. YAML frontmatter provides structured metadata for each document

## Project-Specific Conventions

### Transcript Structure (Mandatory Pattern)
```markdown
## [Month] [Year] – Liberty Jail Entries

![Manuscript page thumbnail](../images/YYYY-MM-DD.jpg)

---
title: "Hyrum Smith Journal – [Month] DD, YYYY"
date: YYYY-MM-DD
location: Liberty Jail, Clay County, Missouri
image_ref: "../images/YYYY-MM-DD.jpg"
image_processed_ref: "../images/processed_full/YYYY-MM-DD.jpg" # enhanced full page (no crop)
image_working_ref: "../images/processed_safe_crop/YYYY-MM-DD.jpg" # enhanced safe-cropped (editor working image)
provenance: "Church History Library, Salt Lake City – MS 9028446 (Hyrum Smith Papers)"
editor: Mark Phillips
# ... additional YAML fields
---

### Faithful (Diplomatic) Transcription
[Preserves original spelling, punctuation, capitalization exactly]

### Modernized (Readable) Transcription  
[Normalized for modern readers while preserving meaning]

---
*Edited and prepared by Mark Phillips, 2025 Digital Edition.*
```

### Editorial Conventions
- **Diplomatic transcription**: Preserve ALL original features (spelling, punctuation, line breaks)
- **Square bracket notation**: `[illegible]`, `[torn]`, `[word?]` for editorial uncertainty
- **Image coupling**: Every transcript must reference its corresponding manuscript image
- **Consistent dating**: Use ISO format (YYYY-MM-DD) throughout filenames and metadata
	- Keep `image_ref` pointing to the original in `images/`
	- Optionally include `image_processed_ref` (enhanced full-page) and `image_working_ref` (safe-cropped) for readability

### Metadata Integrity
- **`date_mapping.json`**: Maps dates to original image UUIDs (critical for provenance)
- **`sources.yml`**: Maintains institutional attribution and rights information
- **YAML frontmatter**: Required fields include `title`, `date`, `location`, `image_ref`, `provenance`, `editor`

## Development Workflows

### Adding New Transcripts
1. Create transcript file: `transcripts/YYYY-MM-DD.md` using the mandatory structure
2. Add corresponding image: `images/YYYY-MM-DD.jpg`
3. Update `metadata/date_mapping.json` with image UUID mapping
4. Update `TOC.md` table with new entry
5. (Optional) Add `image_processed_ref` and `image_working_ref` for improved on-screen transcription

### Quality Assurance
- Verify image-transcript pairing for every date
- Maintain dual transcription structure (diplomatic + modernized)
- Cross-reference dates in TOC.md, transcripts/, and metadata/
- Preserve scholarly apparatus in `docs/` for transparency

### Editorial Standards
- **Accuracy over convenience**: Diplomatic transcriptions are primary sources
- **Transparent methodology**: Document all editorial decisions in `docs/transcription-method.md`
- **Consistent attribution**: Always credit original repository and this digital edition
- **Accessibility**: Modernized versions make content approachable without sacrificing scholarly rigor

## Integration Points
- **Church History Library**: Primary source repository (MS 9028446)
- **Creative Commons licensing**: Text/metadata under CC BY-NC 4.0
- **PDF compilation**: Automated generation from markdown sources (see `compiled/`)

This is a **scholarly preservation project**, not a development codebase. Prioritize historical accuracy, editorial transparency, and long-term digital preservation over software engineering patterns.