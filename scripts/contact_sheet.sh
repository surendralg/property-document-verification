#!/usr/bin/env bash
# Usage: contact_sheet.sh <scan.pdf> <outdir>
# Rasterizes every page, builds 3x3 thumbnail sheets, and OCRs each page (English).
# Needs poppler-utils (pdftoppm), ImageMagick (montage) and tesseract.
set -eu
pdf="$1"; out="$2"
mkdir -p "$out/thumb" "$out/page"
pdftoppm -jpeg -r 50 "$pdf" "$out/thumb/p"
pdftoppm -jpeg -r 200 "$pdf" "$out/page/p"
files=( "$out"/thumb/p-*.jpg ); n=${#files[@]}; i=0; s=0
while [ $i -lt $n ]; do
  montage "${files[@]:$i:9}" -tile 3x3 -geometry 400x520+4+4 -label '%f' "$out/sheet$s.jpg"
  i=$((i+9)); s=$((s+1))
done
for f in "$out"/page/p-*.jpg; do tesseract "$f" "${f%.jpg}" -l eng >/dev/null 2>&1 || true; done
for f in "$out"/page/p-*.txt; do echo "=== $(basename "$f")"; grep -v '^\s*$' "$f" | head -6 | cut -c1-120; done > "$out/ocr_heads.txt"
echo "Pages: $n | sheets: $s | OCR heads: $out/ocr_heads.txt"
