---
name: property-document-verification
description: Verify Indian property title documents and compile a bank-ready property file. Sorts scanned deeds, decrees, khata, tax receipts, ECs, bank mortgage papers and sale agreements; removes duplicates; traces the chain of title; cross-checks the encumbrance certificate; flags title and stamp-duty risks; writes a title report; and builds one indexed, color-coded PDF document set with a cover page. Use this whenever someone is buying, mortgaging or getting a loan on land, a site, a flat or an industrial plot in India and shares property papers (scanned PDFs or photos), asks what documents are missing, asks whether a document "is already there", needs a title or legal-scrutiny style summary, or has to send property documents to a bank, lawyer or buyer. Also use it when adding newly scanned papers to an existing title report or document set.
---

# Property document verification

This skill turns a pile of scanned property papers into two things a bank or advocate can use:

1. A **title report** that traces ownership from the original grant to the current owner, lists encumbrances, and flags problems.
2. A **property document set**: one PDF with a cover page, the report, a document index, and every document in title-chain order with a colored header on each page.

It was written for Karnataka (CITB/MUDA, MCC khata, Kaveri ECs) but the workflow applies across India. Read `references/document-types.md` when a document is unfamiliar.

This is document organization, not a legal opinion. Say so in the report footer and in replies, and suggest an advocate for anything that affects money or title.

## Workflow

### 1. Inventory every page before writing anything

Scans are usually image-only PDFs with no text layer, often 30 to 100 pages of mixed documents.

- Run `scripts/contact_sheet.sh <file.pdf> <outdir>`. It rasterizes pages, builds 3x3 thumbnail sheets, and OCRs every page (English). View the sheets to find document boundaries, then view individual pages at higher resolution only where needed.
- Kannada and Hindi text will not OCR with the default Tesseract install. Read those pages visually; registration numbers, dates and names are usually in Latin digits or English.
- Record for each document: type, date, parties, registration number and office, page range in the source, and whether it is an original, certified copy or notarized copy.

### 2. Deduplicate against what already exists

When the user already has a report or document set, compare by **document identity**, not by file. Same registration number, same decree number, or same date plus issuer means duplicate. Families often hand over the same decree three times (original set, bank set, advocate set). Tell the user which pages were duplicates and which documents are new, so they can answer questions like "was this already there?".

### 3. Build the chain of title

Start at the original grant (development authority allotment, title deed, or earliest sale deed) and walk forward. Every change in holder needs a document: sale deed, gift, partition decree, release, will plus probate, or death plus legal-heir/family-surviving certificate. Write each step as: date, event, holders after the event, source document.

Watch for:
- Heirs who died before the deceased (they drop out) and heirs who were minors at partition.
- Court partition decrees registered at the Sub-Registrar: the registered decree *is* the partition deed. Banks often ask for a "partition deed" with the decree's registration number; explain this rather than searching for a separate deed.
- Related decrees that touch common passages or adjoining portions but not the schedule property. Record them and say plainly whether they affect the schedule property.

### 4. Cross-check encumbrances

Line up every EC entry against a document. Deposits of title deeds (MODTD / "DTD"), letters of continuity, mortgages and releases should each have paper behind them. Note the borrower name, because a property owned by an individual is often security for a firm's loan, and loan closure must cover every facility secured by the property. Confirm that EC periods cover the whole history without gaps.

### 5. Flag risks

Read `references/red-flags.md` and check every item. Typical findings: e-stamp issued after the execution date, stamp duty article not matching an agreement that hands over possession, NPA loans with growing closure amounts, name or relationship errors (S/o vs C/o), area mismatches between decree and khata, buildings the valuer treats as scrap while the khata shows built-up area.

Put flags in the chat reply, not buried in the report, unless the user wants them in the report.

### 6. Write or update the title report

Use the structure in `references/report-template.md`. When a report already exists, edit it in place and keep its format; change only rows the new documents affect, and keep the source-document column accurate. Apply the user's spelling and punctuation preferences.

### 7. Build the property document set

1. Put page images for each document in title-chain (date) order. Keep previously numbered documents in that order too and renumber; date order is easier to audit than "old set then new set".
2. Fill a manifest like `assets/manifest.example.json`: property facts for the cover, chain-of-title lines, categories, and one entry per document with its title, date, category and source pages.
3. Export the title report to PDF if there is one.
4. Run `python scripts/build_bundle.py manifest.json out.pdf`. It renders the cover, inserts the report, writes the index with page numbers, and gives every document page a colored header ("Doc 7 of 31", "Page 2 of 5") and a footer with the overall page number.
5. Render the cover, index and a few document pages to PNG and look at them before sending. Check for overlapping text and titles that shrank too far.
6. Keep the file under about 25 MB if it will be emailed or sent on WhatsApp. Lower `jpeg_quality` or `max_width` in the manifest if needed.

### 8. Help the user communicate

Banks ask for documents by registration number. Answer with the document number in the set and its page range, and point out typos in the request (for example, a wrong SRO prefix or a transposed digit) so the user can correct them politely. Draft short messages that list each requested document with pages.

## Money and loan questions

When a bank asks the buyer to clear the seller's loan first, explain the protections: written in-principle sanction, exact closure figure from the lender, payment directly to the loan account, a seller receipt tying the payment to the sale consideration, no-dues covering every facility, release of original deeds, registered release of each deposit, and a fresh EC. Give facts and options, not a recommendation, and suggest an advocate review.
