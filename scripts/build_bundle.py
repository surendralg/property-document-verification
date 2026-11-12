#!/usr/bin/env python3
"""Build an indexed property document set from a JSON manifest.

Usage: python build_bundle.py manifest.json out.pdf

Produces: cover page, optional title report PDF, document index, then every
document page with a colored header (doc number, title, category, date,
"Page i of n", "Doc k of N") and a footer with the overall page number.
See assets/manifest.example.json for the manifest format.

Needs: reportlab, pypdf, Pillow, and poppler-utils (pdftoppm) for PDF sources.
"""
import io, json, os, subprocess, sys, tempfile, glob
from PIL import Image
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import stringWidth

def find_font(names):
    for d in ['/usr/share/fonts', '/Library/Fonts', 'C:/Windows/Fonts', os.path.expanduser('~/.fonts')]:
        for n in names:
            hits = glob.glob(os.path.join(d, '**', n), recursive=True)
            if hits: return hits[0]
    sys.exit('DejaVuSans fonts not found; install fonts-dejavu or set FONT_DIR')

FONT_DIR = os.environ.get('FONT_DIR')
REG = os.path.join(FONT_DIR, 'DejaVuSans.ttf') if FONT_DIR else find_font(['DejaVuSans.ttf'])
BOLD = os.path.join(FONT_DIR, 'DejaVuSans-Bold.ttf') if FONT_DIR else find_font(['DejaVuSans-Bold.ttf'])
pdfmetrics.registerFont(TTFont('R', REG)); pdfmetrics.registerFont(TTFont('B', BOLD))

W, H = 595.28, 841.89
NAVY = (0.078, 0.212, 0.361); INK = (0.118, 0.141, 0.188); GRAY = (0.357, 0.392, 0.455)
LINE = (0.851, 0.871, 0.902); PALE = (0.953, 0.965, 0.980); SOFT = (0.788, 0.839, 0.910); GOLD = (0.949, 0.702, 0.239)
DEFAULT_CATS = {'Grant': '#1f6fb2', 'Civil records': '#0e9384', 'Court decrees': '#7a3eb1',
                'Khata and tax': '#2e9e4f', 'Encumbrance': '#d9731a', 'Legal opinions': '#b8336a',
                'Bank': '#3b4a63', 'Sale': '#b32121'}

def hexrgb(h): h = h.lstrip('#'); return tuple(int(h[i:i+2], 16) / 255 for i in (0, 2, 4))
def fill(c, col): c.setFillColorRGB(*col)
def shrink(t, font, size, maxw, floor=7):
    while stringWidth(t, font, size) > maxw and size > floor: size -= 0.25
    return size
def wrap(t, font, size, maxw):
    words, lines, cur = t.split(), [], ''
    for w in words:
        nxt = (cur + ' ' + w).strip()
        if stringWidth(nxt, font, size) <= maxw: cur = nxt
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines

def parse_pages(spec, n):
    if not spec: return list(range(1, n + 1))
    out = []
    for part in str(spec).split(','):
        part = part.strip()
        if '-' in part: a, b = part.split('-'); out += list(range(int(a), int(b) + 1))
        else: out.append(int(part))
    return out

def doc_images(d, base, tmp, maxw, q):
    imgs = []
    if 'images' in d:
        srcs = [os.path.join(base, p) for p in d['images']]
    else:
        src = os.path.join(base, d['source']); n = len(PdfReader(src).pages)
        srcs = []
        for p in parse_pages(d.get('pages'), n):
            stem = os.path.join(tmp, f'{abs(hash(src))}_{p}')
            if not os.path.exists(stem + '.jpg'):
                subprocess.run(['pdftoppm', '-jpeg', '-r', '150', '-singlefile', '-f', str(p), '-l', str(p), src, stem], check=True)
            srcs.append(stem + '.jpg')
    for s in srcs:
        im = Image.open(s).convert('RGB')
        if im.width > maxw: im = im.resize((maxw, round(im.height * maxw / im.width)))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=q); b.seek(0); imgs.append(b)
    return imgs

def main(mpath, out):
    m = json.load(open(mpath)); base = os.path.dirname(os.path.abspath(mpath))
    cats = {k: hexrgb(v) for k, v in (m.get('categories') or DEFAULT_CATS).items()}
    footer_text = m.get('footer', m['title'] + '  |  Property document set')
    q = m.get('jpeg_quality', 72); maxw = m.get('max_width', 1240)
    tmp = tempfile.mkdtemp()
    docs = m['documents']
    for d in docs: d['_imgs'] = doc_images(d, base, tmp, maxw, q)
    rep = PdfReader(os.path.join(base, m['report_pdf'])) if m.get('report_pdf') else None
    rp = len(rep.pages) if rep else 0
    first = 1 + rp + 1 + 1; starts = []; p = first
    for d in docs: starts.append(p); p += len(d['_imgs'])
    total = p - 1; N = len(docs)

    def footer(c, pg):
        c.setStrokeColorRGB(*LINE); c.setLineWidth(0.6); c.line(24, H - 811.9, 571.3, H - 811.9)
        fill(c, GRAY); c.setFont('R', 7.5); c.drawString(24, H - 824.7, footer_text)
        c.drawRightString(571.3, H - 824.7, f'Page {pg} of {total}')

    # Cover
    cb = io.BytesIO(); c = canvas.Canvas(cb, pagesize=(W, H))
    fill(c, NAVY); c.rect(0, H - 210, W, 210, stroke=0, fill=1)
    cl = list(cats.values()); bw = W / len(cl)
    for i, col in enumerate(cl): fill(c, col); c.rect(i * bw, H - 216, bw + 1, 6, stroke=0, fill=1)
    fill(c, GOLD); c.setFont('B', 9); c.drawString(40, H - 52.7, 'PROPERTY DOCUMENT SET')
    c.setFillColorRGB(1, 1, 1); s = shrink(m['title'], 'B', 24, 515); c.setFont('B', s); c.drawString(40, H - 89.8, m['title'])
    c.setFont('R', 14); c.drawString(40, H - 112.9, m.get('subtitle', ''))
    fill(c, SOFT); c.setFont('R', 10); y = 140.7
    for line in m.get('cover_lines', []): c.drawString(40, H - y, line); y += 16
    c.drawString(40, H - 182.7, f"{N} documents  |  {total} pages  |  Compiled {m.get('compiled', '')}")
    for k, t in enumerate(m.get('tiles', [])[:6]):
        x = 40 + 178 * (k % 3); top = 244 + 76 * (k // 3); col = cats.get(t.get('category'), NAVY)
        fill(c, PALE); c.roundRect(x, H - top - 64, 166, 64, 4, stroke=0, fill=1)
        fill(c, col); c.rect(x, H - top - 64, 5, 64, stroke=0, fill=1)
        fill(c, GRAY); c.setFont('R', 7.5); c.drawString(x + 14, H - top - 16.8, t['label'].upper())
        fill(c, INK); c.setFont('B', shrink(t['value'], 'B', 14, 145)); c.drawString(x + 14, H - top - 37.4, t['value'])
        fill(c, GRAY); c.setFont('R', shrink(t.get('sub', ''), 'R', 8, 148)); c.drawString(x + 14, H - top - 53.9, t.get('sub', ''))
    yb = 244 + 76 * ((len(m.get('tiles', [])[:6]) + 2) // 3) + 6
    if m.get('boundaries'):
        fill(c, INK); c.setFont('B', 11); c.drawString(40, H - yb - 9.5, 'Boundaries')
        for k, (a, v) in enumerate(list(m['boundaries'].items())[:4]):
            x = 40 + 130.8 * k
            c.setFillColorRGB(1, 1, 1); c.setStrokeColorRGB(*LINE); c.setLineWidth(0.8)
            c.roundRect(x, H - yb - 56, 122.8, 40, 4, stroke=1, fill=1)
            fill(c, cl[0]); c.setFont('B', 8); c.drawString(x + 10, H - yb - 31, a.upper())
            fill(c, INK); c.setFont('R', shrink(v, 'R', 8.5, 105)); c.drawString(x + 10, H - yb - 47, v)
        yb += 80
    chain = m.get('chain', [])
    if chain:
        fill(c, INK); c.setFont('B', 11); c.drawString(40, H - yb - 9.5, m.get('chain_heading', 'Chain of title'))
        y0 = yb + 26; step = min(40, (790 - y0) / max(len(chain), 1))
        c.setStrokeColorRGB(*LINE); c.setLineWidth(2); c.line(112, H - y0, 112, H - y0 - step * (len(chain) - 1) - 4)
        for i, e in enumerate(chain):
            y = y0 + step * i; col = cats.get(e.get('category'), NAVY)
            c.setFillColorRGB(1, 1, 1); c.setStrokeColorRGB(*col); c.setLineWidth(2.2); c.circle(112, H - y - 4, 5.5, stroke=1, fill=1)
            fill(c, col); c.circle(112, H - y - 4, 2.6, stroke=0, fill=1)
            c.setFont('B', 9); c.drawRightString(97, H - y - 7.7, e['year'])
            fill(c, INK); c.setFont('B', 9.5); c.drawString(128, H - y - 7.8, e['title'])
            fill(c, GRAY); c.setFont('R', 8)
            c.drawString(128, H - y - 20.1, wrap(e.get('detail', ''), 'R', 8, 427)[0] if e.get('detail') else '')
    if m.get('prepared_by'):
        fill(c, GRAY); c.setFont('R', 8); c.drawRightString(555.3, H - 802.8, f"Prepared by {m['prepared_by']}")
    footer(c, 1); c.save()

    # Index (two pages if needed)
    ib = io.BytesIO(); c = canvas.Canvas(ib, pagesize=(W, H))
    pitch = max(16, min(29, 676 / N)); per_page = int(676 // pitch)
    idx_pg = 1 + rp + 1
    for chunk in range(0, N, per_page):
        fill(c, NAVY); c.rect(0, H - 70, W, 70, stroke=0, fill=1)
        c.setFillColorRGB(1, 1, 1); c.setFont('B', 18); c.drawString(40, H - 45.3, 'Document index')
        fill(c, SOFT); c.setFont('R', 9); c.drawRightString(555.3, H - 44.7, 'In date order of the title chain')
        x = 40
        for name, col in cats.items():
            fill(c, col); c.roundRect(x, H - 92.5, 8, 8, 2, stroke=0, fill=1)
            fill(c, INK); c.setFont('R', 7.5); c.drawString(x + 12, H - 92.6, name); x += 26 + stringWidth(name, 'R', 7.5)
        fill(c, GRAY); c.setFont('B', 7.5)
        for xx, t in ((40, 'NO.'), (76, 'DOCUMENT'), (400, 'DATE')): c.drawString(xx, H - 116.6, t)
        c.drawRightString(555.3, H - 116.6, 'PAGES')
        c.setStrokeColorRGB(*LINE); c.setLineWidth(0.8); c.line(40, H - 122, 555.3, H - 122)
        for r, i in enumerate(range(chunk, min(N, chunk + per_page))):
            d = docs[i]; y = 124 + pitch * r; col = cats.get(d['category'], NAVY)
            if r % 2 == 0:
                fill(c, PALE); c.setStrokeColorRGB(*LINE); c.setLineWidth(0.5); c.rect(40, H - y - pitch, 515.3, pitch, stroke=1, fill=1)
            mid = H - y - pitch / 2
            fill(c, col); c.roundRect(44, mid - 6.5, 20, 13, 3, stroke=0, fill=1)
            c.setFillColorRGB(1, 1, 1); c.setFont('B', 8); c.drawCentredString(54, mid - 3, f'{i + 1:02d}')
            fill(c, INK); c.setFont('R', shrink(d['title'], 'R', 8.5, 318)); c.drawString(76, mid - 3, d['title'])
            fill(c, GRAY); c.setFont('R', 8.5); c.drawString(400, mid - 3, d['date'])
            a = starts[i]; e = a + len(d['_imgs']) - 1
            fill(c, INK); c.setFont('B', 8.5); c.drawRightString(555.3, mid - 3, str(a) if a == e else f'{a} - {e}')
        footer(c, idx_pg); c.showPage()
    c.save()
    if PdfReader(io.BytesIO(ib.getvalue())).pages.__len__() > 1:
        sys.exit('Index needs more than one page; shorten titles or split documents. Page numbers assume a one-page index.')

    # Document pages
    db = io.BytesIO(); c = canvas.Canvas(db, pagesize=(W, H))
    for i, d in enumerate(docs):
        col = cats.get(d['category'], NAVY); n = len(d['_imgs'])
        for j, imgb in enumerate(d['_imgs']):
            fill(c, col); c.rect(0, H - 50, W, 50, stroke=0, fill=1)
            c.saveState(); c.setFillColorRGB(0, 0, 0); c.setFillAlpha(0.18); c.rect(0, H - 50, 74, 50, stroke=0, fill=1); c.restoreState()
            c.setFillColorRGB(1, 1, 1); c.setFont('B', 7); c.drawCentredString(37, H - 18.7, 'DOC')
            c.setFont('B', 18); c.drawCentredString(37, H - 40.3, f'{i + 1:02d}')
            c.setFont('B', shrink(d['title'], 'B', 11.5, 412, 8)); c.drawString(88, H - 23.3, d['title'])
            c.setFont('R', 8.5); c.drawString(88, H - 38.8, f"{d['category']}  |  Dated {d['date']}")
            c.setFont('B', 9); c.drawRightString(577, H - 22.8, f'Page {j + 1} of {n}')
            c.setFont('R', 7.5); c.drawRightString(577, H - 36.6, f'Doc {i + 1} of {N}')
            ir = ImageReader(imgb); iw, ih = ir.getSize()
            sc = min(525 / iw, 740 / ih); w, h = iw * sc, ih * sc
            x = 35.1 + (525 - w) / 2; yt = 62 + (740 - h) / 2
            c.setFillColorRGB(1, 1, 1); c.setStrokeColorRGB(*LINE); c.setLineWidth(0.6); c.rect(x, H - yt - h, w, h, stroke=1, fill=1)
            c.drawImage(ir, x, H - yt - h, w, h)
            footer(c, starts[i] + j); c.showPage()
    c.save()

    wr = PdfWriter()
    for blob in (cb.getvalue(),):
        for pg in PdfReader(io.BytesIO(blob)).pages: wr.add_page(pg)
    if rep:
        for pg in rep.pages: wr.add_page(pg)
    for blob in (ib.getvalue(), db.getvalue()):
        for pg in PdfReader(io.BytesIO(blob)).pages: wr.add_page(pg)
    wr.add_metadata({'/Title': m['title'] + ' - Property document set', '/Author': m.get('prepared_by', '')})
    wr.write(out)
    print(f'{out}: {len(wr.pages)} pages, {N} documents, {os.path.getsize(out) / 1e6:.1f} MB')

if __name__ == '__main__':
    if len(sys.argv) != 3: sys.exit(__doc__)
    main(sys.argv[1], sys.argv[2])
