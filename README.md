# Property Document Verification skill

A Claude skill for verifying Indian property title documents and compiling a bank-ready property file.

Give Claude a stack of scanned property papers (deeds, court decrees, khata, tax receipts, encumbrance certificates, bank mortgage papers, sale agreement) and it will:

- inventory every page of image-only scans, with thumbnail sheets and OCR
- drop duplicates and report which documents are new
- trace the chain of title from the original grant to the current owner
- match every encumbrance certificate entry to a document
- flag common risks (e-stamp dated after execution, stamp duty article, NPA loans, firm borrowers, name and area mismatches)
- write or update a title report
- build one indexed PDF: cover page, title report, document index, and every document with a color-coded header and page numbers

Written for Karnataka (CITB/MUDA, MCC khata, Kaveri ECs); the workflow applies across India.

> This skill organizes documents. It does not give legal opinions. Have an advocate review title and payment decisions.

## Contents

```
property-document-verification/
├── SKILL.md                      workflow Claude follows
├── references/
│   ├── document-types.md         glossary of Indian property documents
│   ├── red-flags.md              review checklist
│   └── report-template.md        title report structure
├── scripts/
│   ├── contact_sheet.sh          rasterize, thumbnail and OCR scanned PDFs
│   └── build_bundle.py           manifest-driven PDF document set builder
└── assets/
    └── manifest.example.json     sample manifest (fictional data)
```

## Install

**Claude.ai / Claude desktop**

1. Download `property-document-verification.skill` from the [latest release](https://github.com/surendralg/property-document-verification/releases/latest).
2. In Claude, open Settings > Capabilities > Skills and upload the file.

**Claude Code**

```bash
git clone https://github.com/surendralg/property-document-verification ~/.claude/skills/property-document-verification
```

Or copy the folder into `.claude/skills/` inside a project to make it available only there.

**Rebuilding the package yourself**

The `.skill` file is a zip of this folder. From the folder's parent directory:

```bash
zip -r property-document-verification.skill property-document-verification -x "*/.git/*" "*/dist/*" "*.skill"
```

## Using the bundle builder on its own

Requirements: Python 3.9+, `pip install reportlab pypdf pillow`, plus `poppler-utils`, ImageMagick and Tesseract for the scan tools.

```bash
./scripts/contact_sheet.sh scans/new_scan.pdf work/
python scripts/build_bundle.py manifest.json Property_File.pdf
```

Each document in the manifest takes either `source` (PDF path) with optional `pages` ("1-5,8"), or `images` (list of image paths). Documents appear in the order listed, so list them in title-chain date order.

## Privacy

Property files contain names, addresses, PAN fragments, loan account numbers and registration numbers. Never commit real scans, manifests or generated files. The `.gitignore` excludes common output paths; keep real data outside the repo.

## License

MIT
