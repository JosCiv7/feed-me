"""Volledige artikeltekst ophalen, zodat je het artikel in de app zelf kan lezen.

Betaal- en loginmuren worden gerespecteerd: als een site aangeeft dat een artikel niet gratis is
(isAccessibleForFree: false), een inlog- of privacypagina toont of ons weigert, bewaren we geen tekst
en verwijst de app gewoon naar de site zelf.
"""
import html
import json
import re
from pathlib import Path

try:
    import trafilatura
    AVAILABLE = True
except ImportError:
    AVAILABLE = False

from translate import read_json, write_json  # noqa: E402  (veilig lezen en schrijven van cachebestanden)

CACHE_FILE = Path(__file__).resolve().parent / "cache" / "articles.json"
MIN_WORDS = 120

PAYWALL_RE = re.compile(r'"isAccessibleForFree"\s*:\s*"?false', re.I)
WALL_TITLE_RE = re.compile(r"<title>[^<]*(inloggen|log in|sign in|privacy gate|consent|abonne|subscribe)[^<]*</title>", re.I)

# Losse regels rond het artikel die geen deel van het verhaal zijn
JUNK_RE = re.compile(
    r"^(- )?(published|updated|gepubliceerd|bijgewerkt|publié|mis à jour)\b"
    r"|\b(sign up|subscribe|newsletter|nieuwsbrief|inscrivez-vous|abonneer|abonnez-vous|click here|klik hier"
    r"|read more|lees ook|lees meer|à lire aussi|lire aussi|related:|follow us|volg ons|share this|deel dit"
    r"|have you been affected|exclusive content|support our journalism|steun onze)\b"
    r"|^(advertisement|advertentie|publicité|getty images|foto:|photo:|©)",
    re.I,
)


def load_cache():
    return read_json(CACHE_FILE)


def save_cache(cache, keep_links):
    write_json(CACHE_FILE, {k: v for k, v in cache.items() if k in keep_links})


def extract(page):
    """Geeft (paragrafen, reden) terug; paragrafen is leeg als er geen bruikbare vrije tekst is."""
    if PAYWALL_RE.search(page):
        return [], "betaalmuur"
    if WALL_TITLE_RE.search(page[:20000]):
        return [], "inlogmuur"
    text = trafilatura.extract(page, include_comments=False, include_tables=False, favor_precision=True) or ""
    paras = []
    for p in text.split("\n"):
        p = re.sub(r"\s+", " ", p).strip()
        if len(p) < 3 or (JUNK_RE.search(p) and len(p) < 250):
            continue
        if p not in paras:
            paras.append(p)
    if sum(len(p.split()) for p in paras) < MIN_WORDS:
        return [], "te kort"
    return paras, None


def trim_head(paras, title):
    """Haal de titel en losse labels ("Wereld", "Politiek") weg die soms vóór het artikel staan."""
    norm = lambda s: re.sub(r"\W+", "", s.lower())
    t = norm(title)
    i = 0
    while i < len(paras) and i < 4:
        p = paras[i]
        if norm(p) == t or (t and norm(p) in t and len(p) > 20) or (len(p) < 40 and not re.search(r"[.!?:]$", p)):
            i += 1
        else:
            break
    return paras[i:]


def og_image(page):
    for p in (r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"',
              r'<meta[^>]+name="twitter:image"[^>]+content="([^"]+)"'):
        m = re.search(p, page, re.I)
        if m:
            return html.unescape(m.group(1))
    return ""


def download(link, fetch):
    """Enkel de pagina downloaden (mag in parallelle draden): geeft (pagina, fout)."""
    try:
        return fetch(link, limit=1_500_000, timeout=15), None
    except Exception as e:
        return None, e


def get(link, fetch):
    """Haal één artikel op (tekst + foto); geeft een cache-item terug."""
    return parse(*download(link, fetch))


def parse(page, error=None):
    """Tekst en foto uit een gedownloade pagina halen. Altijd in de hoofddraad: de tekstlezer (lxml) liep in parallelle
    draden af en toe vast met een crash ("free(): invalid pointer", 17/11/2026 op GitHub en 23/11 lokaal)."""
    if page is None:
        reason = "geweigerd" if any(c in str(error) for c in ("401", "403", "429")) else "niet bereikbaar"
        return {"p": [], "why": reason, "img": "", "retry": reason == "niet bereikbaar"}
    paras, why = extract(page) if AVAILABLE else ([], "geen tekstlezer")
    site = re.search(r'<meta[^>]+property="og:site_name"[^>]+content="([^"]+)"', page, re.I)
    return {"p": paras, "why": why, "img": og_image(page), "site": html.unescape(site.group(1)).strip() if site else ""}
