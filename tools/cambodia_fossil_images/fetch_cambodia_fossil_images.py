#!/usr/bin/env python3
"""
Download reusable photos and figures for the Cambodia fossil report.

  A) Open-access MDPI figures (CC BY 4.0): Lim et al. 2023 and Tong et al. 2026
  B) Wikimedia Commons photos (only CC BY / CC BY-SA / CC0 / Public domain / GFDL)
  C) Mansuy 1914 fossil plates (public domain), rendered at 300 dpi with PyMuPDF

Outputs in the output folder:
  credits.csv   file, what_it_shows, author/credit, licence, source_url
  index.html    contact sheet showing every image with its credit
  failures.txt  everything that was skipped and why

Requirements:   pip install requests pymupdf
Usage:          python fetch_cambodia_fossil_images.py [--out DIR] [--plates 40-62]
                                                     [--extra 5] [--only A,B,C]
"""

import argparse
import csv
import html
import os
import re
import sys
import time
import urllib.parse
from pathlib import Path

try:
    import requests
except ImportError:
    sys.exit("This script needs 'requests':  pip install requests")

# --------------------------------------------------------------------------- #
# Settings
# --------------------------------------------------------------------------- #
DELAY_S = 2.0          # wait between HTTP requests
TIMEOUT_S = 60
BROWSER_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")
# Wikimedia asks scripts to identify themselves rather than pose as a browser.
WIKI_UA = ("GDMG-CambodiaFossilReport/1.0 (personal research script; "
           "https://commons.wikimedia.org/wiki/Commons:Reusing_content_outside_Wikimedia) "
           "python-requests/" + requests.__version__)

LIM2023 = ("Lim, V., Buffetaut, E., Tong, H., Cavin, L., Pann, K. & Ngoeun, P.P. (2023). "
           "The first dinosaur from the Kingdom of Cambodia. Fossil Studies 1(1): 49-59. "
           "doi:10.3390/fossils1010006")
TONG2026 = ("Tong, H., Buffetaut, E., Lim, V., Philippe, M., Boonchai, N. & Claude, J. (2026). "
            "Turtle remains from Koh Moul (SW Cambodia) and their stratigraphical implications. "
            "Diversity 18(5): 249. doi:10.3390/d18050249")
MANSUY1914 = ("Mansuy, H. (1914). Faunes des calcaires a Productus de l'Indochine, 2e serie. "
              "Memoires du Service geologique de l'Indochine 3. Scan: Sorbonne Universite, "
              "patrimoine.sorbonne-universite.fr")

MDPI_LIM = "https://mdpi-res.com/fossstud/fossstud-01-00006/article_deploy/html/images/"
PART_A = [
    ("01_Lim2023_Fig1_KohPaur_location.jpg", MDPI_LIM + "fossstud-01-00006-g001-550.jpg",
     "Lim et al. 2023 Fig. 1 - location of the Koh Paur dinosaur site, Koh Kong"),
    ("02_Lim2023_Fig2_KohKong_geomap.jpg", MDPI_LIM + "fossstud-01-00006-g002-550.jpg",
     "Lim et al. 2023 Fig. 2 - geological map of the Koh Kong area"),
    ("03_Lim2023_Fig3_sauropod_fibula_in_situ.jpg", MDPI_LIM + "fossstud-01-00006-g003-550.jpg",
     "Lim et al. 2023 Fig. 3 - sauropod fibula in situ"),
    ("04_Lim2023_Fig4_sauropod_fibula_views.jpg", MDPI_LIM + "fossstud-01-00006-g004-550.jpg",
     "Lim et al. 2023 Fig. 4 - sauropod fibula in several views"),
]
TONG_PAGE = "https://www.mdpi.com/1424-2818/18/5/249/htm"

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMONS_FILES = [
    "File:Cave_statue_in_Phnom_Sampeau_(Battambang,_Cambodia_2011).jpg",
    "File:04-Phnom_Sorsia,_Kampot-nX-5.jpg",
    "File:Yak_Loum.jpg",
]
COMMONS_SEARCH = ["Phnom Sampov", "Kampot caves", "Phnom Chhngok", "Bokor plateau sandstone",
                  "Koh Kong Cardamom sandstone", "Laang Spean", "petrified wood Cambodia"]

MANSUY_PDF = ("https://patrimoine.sorbonne-universite.fr/medias/fe/df/6a/a2/"
              "fedf6aa2-7028-426e-b0e1-256f32fa7b03/files/P395_15.pdf")

# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
credits = []    # dicts with keys file, what_it_shows, credit, licence, source_url
failures = []   # (item, reason)
_last_request = [0.0]


def default_out_dir():
    if os.name == "nt" and os.path.isdir("D:\\"):
        return Path(r"D:\GDMG_Library\Cambodia_Fossil_Images")
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    return home / "Documents" / "GDMG_Library" / "Cambodia_Fossil_Images"


def make_session(ua):
    s = requests.Session()
    s.headers.update({"User-Agent": ua,
                      "Accept-Language": "en-GB,en;q=0.9"})
    return s


WEB = make_session(BROWSER_UA)
WIKI = make_session(WIKI_UA)


def get(session, url, **kw):
    """GET with a polite 2-second gap between all requests."""
    wait = DELAY_S - (time.monotonic() - _last_request[0])
    if wait > 0:
        time.sleep(wait)
    try:
        r = session.get(url, timeout=TIMEOUT_S, **kw)
    finally:
        _last_request[0] = time.monotonic()
    r.raise_for_status()
    return r


def image_kind(data):
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    return None


def fail(item, reason):
    print(f"   FAILED: {item}: {reason}")
    failures.append((item, str(reason)))


def add_credit(file, what, credit, licence, url):
    credits.append({"file": file, "what_it_shows": what, "author/credit": credit,
                    "licence": licence, "source_url": url})


def fetch_image(session, url, referer=None):
    """Return (bytes, kind) or raise. kind is 'jpg' or 'png'."""
    headers = {"Accept": "image/avif,image/webp,image/png,image/jpeg,*/*;q=0.8"}
    if referer:
        headers["Referer"] = referer
    r = get(session, url, headers=headers)
    kind = image_kind(r.content)
    if not kind:
        ctype = r.headers.get("Content-Type", "?")
        raise ValueError(f"not a JPEG/PNG (Content-Type {ctype}, first bytes {r.content[:8]!r})")
    return r.content, kind


def save(out, name, data):
    (out / name).write_bytes(data)
    print(f"   saved {name}  ({len(data) / 1024:.0f} KB)")


def strip_html(s):
    s = re.sub(r"<[^>]+>", "", s or "")
    return re.sub(r"\s+", " ", html.unescape(s)).strip()


def safe_name(s, maxlen=80):
    s = re.sub(r"[^\w.\-]+", "_", s, flags=re.UNICODE).strip("_")
    return s[:maxlen]


# --------------------------------------------------------------------------- #
# A) MDPI figures
# --------------------------------------------------------------------------- #
def mdpi_best(url_550, stem, out, referer):
    """Download the -550.jpg and the full .png; keep the bigger one. Returns filename."""
    candidates = []
    try:
        candidates.append((url_550,) + fetch_image(WEB, url_550, referer))
    except Exception as e:
        fail(f"{stem} (550 px) {url_550}", e)
    if url_550.endswith("-550.jpg"):
        big_url = url_550[:-len("-550.jpg")] + ".png"
        try:
            candidates.append((big_url,) + fetch_image(WEB, big_url, referer))
        except Exception as e:      # optional: not a failure if only the 550 px exists
            print(f"   note: no larger .png for {stem} ({e})")
    if not candidates:
        return None, None
    url, data, kind = max(candidates, key=lambda c: len(c[1]))
    name = f"{stem}.{kind}"
    save(out, name, data)
    return name, url


def part_a(out):
    print("\n== A) Open-access MDPI figures (CC BY 4.0)")
    article = "https://www.mdpi.com/"
    for fname, url, what in PART_A:
        stem = fname.rsplit(".", 1)[0]
        name, used = mdpi_best(url, stem, out, article)
        if name:
            add_credit(name, what, LIM2023, "CC BY 4.0", used)

    print(f"-- Tong et al. 2026: reading {TONG_PAGE}")
    try:
        page = get(WEB, TONG_PAGE, headers={"Accept": "text/html"}).text
    except Exception as e:
        fail(f"Tong 2026 article page {TONG_PAGE}", e)
        return
    srcs = re.findall(r"""(?:src|data-src|data-large|data-lsrc|href)\s*=\s*["']([^"']*"""
                      r"""article_deploy/html/images/[^"']+)["']""", page, flags=re.I)
    urls = []
    for src in srcs:
        u = urllib.parse.urljoin(TONG_PAGE, html.unescape(src)).split("?")[0]
        m = re.match(r"(.*-g\d+[a-z]?)(?:-550)?\.(?:jpg|png)$", u)
        if m:                       # always start from the 550-px preview URL
            u = m.group(1) + "-550.jpg"
        if u not in urls and re.search(r"\.(jpg|png)$", u):
            urls.append(u)
    if not urls:
        fail("Tong 2026 figures", "no <img> under article_deploy/html/images/ found on page "
             "(MDPI may have served a bot-check page; open the page in a browser and retry)")
        return
    print(f"   found {len(urls)} figure image(s)")
    for i, u in enumerate(urls, 1):
        m = re.search(r"-g(\d+)([a-z]?)-550\.jpg$", u)
        label = f"{int(m.group(1))}{m.group(2)}" if m else str(i)
        stem = f"05_Tong2026_Fig{label}"
        caption = mdpi_caption(page, u) or f"Tong et al. 2026 Fig. {label}"
        name, used = mdpi_best(u, stem, out, TONG_PAGE)
        if name:
            add_credit(name, caption, TONG2026, "CC BY 4.0", used)


def mdpi_caption(page, img_url):
    """Best-effort: pull the 'Figure N. ...' caption that follows the image in the HTML."""
    base = img_url.rsplit("/", 1)[-1].replace("-550.jpg", "")
    i = page.find(base)
    if i < 0:
        return None
    m = re.search(r"<b>\s*(Figure\s*\d+[a-z]?\.)\s*</b>(.*?)</div>", page[i:i + 20000],
                  flags=re.S | re.I)
    if not m:
        return None
    text = strip_html(m.group(1) + " " + m.group(2))
    return "Tong et al. 2026 " + (text[:220] + "..." if len(text) > 220 else text)


# --------------------------------------------------------------------------- #
# B) Wikimedia Commons
# --------------------------------------------------------------------------- #
def licence_ok(lic):
    l = (lic or "").lower().replace("-", " ")
    if " nc" in f" {l}" or " nd" in f" {l}" or "noncommercial" in l or "no deriv" in l:
        return False
    return (l.startswith("cc by") or l.startswith("cc0") or "public domain" in l
            or l.startswith("pd") or "gfdl" in l)


def commons_query(params):
    p = {"action": "query", "format": "json", "prop": "imageinfo",
         "iiprop": "url|extmetadata|mime|size"}
    p.update(params)
    r = get(WIKI, COMMONS_API, params=p)
    return list(r.json().get("query", {}).get("pages", {}).values())


def commons_download(page, out, prefix, what_default):
    title = page.get("title", "?")
    if "imageinfo" not in page:
        fail(title, "file not found on Commons")
        return False
    ii = page["imageinfo"][0]
    meta = ii.get("extmetadata", {})
    lic = strip_html(meta.get("LicenseShortName", {}).get("value", ""))
    artist = strip_html(meta.get("Artist", {}).get("value", "")) or \
        strip_html(meta.get("Credit", {}).get("value", "")) or "unknown"
    if not licence_ok(lic):
        fail(title, f"licence not reusable: '{lic or 'none given'}'")
        return False
    if ii.get("mime") not in ("image/jpeg", "image/png"):
        fail(title, f"not a JPEG/PNG ({ii.get('mime')})")
        return False
    try:
        data, kind = fetch_image(WIKI, ii["url"])
    except Exception as e:
        fail(f"{title} {ii.get('url')}", e)
        return False
    stem = safe_name(title.split(":", 1)[-1].rsplit(".", 1)[0])
    name = f"{prefix}{stem}.{kind}"
    save(out, name, data)
    desc = strip_html(meta.get("ImageDescription", {}).get("value", ""))
    what = (desc[:200] + "...") if len(desc) > 200 else (desc or what_default)
    add_credit(name, what, artist + " / Wikimedia Commons", lic,
               ii.get("descriptionurl") or ii["url"])
    return True


def part_b(out, extra_limit):
    print("\n== B) Wikimedia Commons")
    done = set()
    for t in COMMONS_FILES:
        print(f"-- {t}")
        try:
            pages = commons_query({"titles": t})
        except Exception as e:
            fail(t, e)
            continue
        for p in pages:
            done.add(p.get("title"))
            commons_download(p, out, "B_", t.split(":", 1)[-1].replace("_", " "))

    extras = 0
    for term in COMMONS_SEARCH:
        if extras >= extra_limit:
            break
        print(f"-- search: \"{term}\"")
        try:
            pages = commons_query({"generator": "search", "gsrsearch": term,
                                   "gsrnamespace": 6, "gsrlimit": 10})
        except Exception as e:
            fail(f"Commons search '{term}'", e)
            continue
        pages.sort(key=lambda p: p.get("index", 0))
        if not pages:
            print("   no results")
        for p in pages:
            if extras >= extra_limit:
                break
            if p.get("title") in done:
                continue
            done.add(p.get("title"))
            ii = (p.get("imageinfo") or [{}])[0]
            lic = strip_html(ii.get("extmetadata", {}).get("LicenseShortName", {}).get("value", ""))
            # Search hits that don't qualify are just passed over, not failures.
            if ii.get("mime") not in ("image/jpeg", "image/png") or not licence_ok(lic):
                continue
            if commons_download(p, out, "B_search_", f"Commons search result for '{term}'"):
                extras += 1
    print(f"   {extras} extra file(s) from searches")


# --------------------------------------------------------------------------- #
# C) Mansuy 1914 plates
# --------------------------------------------------------------------------- #
ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(s):
    s = s.upper()
    if not s or any(c not in ROMAN for c in s):
        return None
    total = 0
    for i, c in enumerate(s):
        v = ROMAN[c]
        total += -v if i + 1 < len(s) and ROMAN[s[i + 1]] > v else v
    return total


def parse_pages(spec, n):
    pages = []
    for part in spec.split(","):
        part = part.strip()
        if "-" in part:
            a, b = part.split("-", 1)
            pages += range(int(a), int(b) + 1)
        elif part:
            pages.append(int(part))
    return [p - 1 for p in pages if 1 <= p <= n]   # to 0-based


EXPL_RE = re.compile(r"EXPLICATION\s+DE\s+LA\s+PLANCHE\s+([IVXLC]+|\d+)", re.I)


def find_plates(doc):
    """Return list of (plate_no, plate_page_idx, explanation_text)."""
    texts = [doc[i].get_text("text") for i in range(doc.page_count)]
    plates = []
    for i, t in enumerate(texts):
        m = EXPL_RE.search(t)
        if not m:
            continue
        num = m.group(1)
        no = int(num) if num.isdigit() else roman_to_int(num)
        # Plate is normally the next page with little or no text (after any
        # continuation of the explanation).
        j = i + 1
        expl = t.strip()
        while j < doc.page_count and len(texts[j].strip()) > 400 and not EXPL_RE.search(texts[j]):
            expl += "\n\n" + texts[j].strip()
            j += 1
        if j < doc.page_count and not EXPL_RE.search(texts[j]):
            plates.append((no, j, expl))
    return plates, texts


def part_c(out, plate_spec):
    print("\n== C) Mansuy 1914 plates (public domain)")
    try:
        import pymupdf as fitz
    except ImportError:
        fail("Mansuy 1914", "PyMuPDF not installed:  pip install pymupdf")
        return
    pdf_dir = out / "_source_pdf"
    pdf_dir.mkdir(exist_ok=True)
    pdf_path = pdf_dir / "Mansuy1914_P395_15.pdf"
    if pdf_path.exists() and pdf_path.read_bytes()[:5] == b"%PDF-":
        print(f"   using cached {pdf_path.name}")
    else:
        try:
            r = get(WEB, MANSUY_PDF, headers={"Accept": "application/pdf"})
            if r.content[:5] != b"%PDF-":
                raise ValueError(f"not a PDF (Content-Type {r.headers.get('Content-Type')})")
            pdf_path.write_bytes(r.content)
            print(f"   downloaded PDF ({len(r.content) / 1e6:.1f} MB)")
        except Exception as e:
            fail(f"Mansuy 1914 PDF {MANSUY_PDF}", e)
            return

    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        fail("Mansuy 1914 PDF", f"cannot open: {e}")
        return
    print(f"   {doc.page_count} pages")

    if plate_spec:
        idxs = parse_pages(plate_spec, doc.page_count)
        texts = [doc[i].get_text("text") for i in range(doc.page_count)]
        plates = []
        for k, i in enumerate(idxs, 1):
            prev = texts[i - 1].strip() if i > 0 and EXPL_RE.search(texts[i - 1]) else ""
            plates.append((k, i, prev))
    else:
        plates, texts = find_plates(doc)
        if not plates:
            has_text = sum(len(t.strip()) for t in texts) > 200 * max(1, doc.page_count // 4)
            why = ("no 'EXPLICATION DE LA PLANCHE' pages found" if has_text else
                   "PDF has no text layer, so plates cannot be detected automatically")
            fail("Mansuy 1914 plate detection",
                 why + ". Open the PDF, note the plate page numbers and rerun with "
                       "e.g. --only C --plates 120-135")
            return
    print(f"   rendering {len(plates)} plate page(s) at 300 dpi")

    seen = set()
    for no, idx, expl in plates:
        label = no if no and no not in seen else f"p{idx + 1}"
        seen.add(no)
        stem = f"C_Mansuy1914_Pl{label}"
        try:
            pix = doc[idx].get_pixmap(dpi=300)
            pix.save(out / f"{stem}.png")
            print(f"   saved {stem}.png  (PDF page {idx + 1}, {pix.width}x{pix.height})")
        except Exception as e:
            fail(f"{stem} (PDF page {idx + 1})", e)
            continue
        if expl:
            (out / f"{stem}_explanation.txt").write_text(expl + "\n", encoding="utf-8")
        else:
            fail(f"{stem} explanation text", "no explanation text found on the preceding page")
        first = re.sub(r"\s+", " ", expl)[:160] if expl else ""
        add_credit(f"{stem}.png",
                   f"Mansuy 1914, Planche {no} (PDF page {idx + 1})" +
                   (f" - {first}..." if first else ""),
                   MANSUY1914, "Public domain (published 1914; author d. before 1955)",
                   MANSUY_PDF)


# --------------------------------------------------------------------------- #
# Outputs
# --------------------------------------------------------------------------- #
def write_outputs(out):
    with open(out / "credits.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=["file", "what_it_shows", "author/credit",
                                          "licence", "source_url"])
        w.writeheader()
        w.writerows(credits)

    with open(out / "failures.txt", "w", encoding="utf-8") as f:
        if not failures:
            f.write("No failures.\n")
        for item, reason in failures:
            f.write(f"{item}\n    {reason}\n")

    cards = []
    for c in credits:
        e = {k: html.escape(v) for k, v in c.items()}
        cards.append(f"""
  <figure>
    <a href="{e['file']}"><img src="{e['file']}" loading="lazy" alt="{e['what_it_shows']}"></a>
    <figcaption>
      <b>{e['file']}</b><br>{e['what_it_shows']}<br>
      <span class="cr">&copy; {e['author/credit']}</span><br>
      <span class="lic">{e['licence']}</span> &middot;
      <a href="{e['source_url']}">source</a>
    </figcaption>
  </figure>""")
    fail_html = "".join(f"<li><b>{html.escape(i)}</b>: {html.escape(r)}</li>" for i, r in failures)
    page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>Cambodia fossil images - contact sheet</title>
<style>
 body {{ font-family: Segoe UI, Arial, sans-serif; margin: 24px; color: #222; }}
 .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 18px; }}
 figure {{ margin: 0; border: 1px solid #ddd; border-radius: 6px; padding: 8px; background: #fafafa; }}
 img {{ width: 100%; height: 220px; object-fit: contain; background: #fff; }}
 figcaption {{ font-size: 12px; line-height: 1.4; margin-top: 6px; word-wrap: break-word; }}
 .cr {{ color: #555; }} .lic {{ color: #0a6; font-weight: 600; }}
</style></head><body>
<h1>Cambodia fossil images</h1>
<p>{len(credits)} image(s). Full credits in <a href="credits.csv">credits.csv</a>;
failures in <a href="failures.txt">failures.txt</a>.</p>
<div class="grid">{''.join(cards)}
</div>
<h2>Failures ({len(failures)})</h2><ul>{fail_html or '<li>None</li>'}</ul>
</body></html>
"""
    (out / "index.html").write_text(page, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=None, help="output folder")
    ap.add_argument("--only", default="A,B,C", help="parts to run, e.g. A,C")
    ap.add_argument("--extra", type=int, default=5,
                    help="max extra Commons files from the searches (default 5)")
    ap.add_argument("--plates", default=None,
                    help="Mansuy PDF page numbers to render as plates, e.g. 120-135,140 "
                         "(default: detect from 'EXPLICATION DE LA PLANCHE' pages)")
    args = ap.parse_args()

    out = args.out or default_out_dir()
    out.mkdir(parents=True, exist_ok=True)
    print(f"Output folder: {out}")
    parts = {p.strip().upper() for p in args.only.split(",")}

    try:
        if "A" in parts:
            part_a(out)
        if "B" in parts:
            part_b(out, args.extra)
        if "C" in parts:
            part_c(out, args.plates)
    except KeyboardInterrupt:
        fail("run", "interrupted by user")
    finally:
        write_outputs(out)
    print(f"\nDone: {len(credits)} image(s), {len(failures)} failure(s).")
    print(f"Open {out / 'index.html'}")


if __name__ == "__main__":
    main()
