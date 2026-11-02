"""Zoekt een gratis versie van nieuws dat enkel achter een betaal- of loginmuur staat.

De muur zelf wordt niet omzeild. We gebruiken enkel de titel en de korte samenvatting uit de RSS-feed
om via Bing Nieuws (openbare RSS, geen account nodig) andere media te vinden die hetzelfde nieuws
gratis brengen. Een gevonden artikel moet zelf vrij leesbaar zijn en genoeg op het origineel lijken.
"""
import json
import math
import re
import time
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path

CACHE_FILE = Path(__file__).resolve().parent / "cache" / "search.json"
SEARCH_URL = "https://www.bing.com/news/search?format=rss&setlang=nl-BE&cc=BE&q="
MAX_SEARCHES = 40          # zoekopdrachten per run (rustig voor Bing)
MAX_CANDIDATES = 4         # artikels per zoekopdracht die we proberen te lezen
RETRY_AFTER_H = 6          # niets gevonden? later nog eens proberen (nieuws komt soms later online)
WALLS = {"betaalmuur", "inlogmuur", "geweigerd", "te kort"}
# doorgeefluiken, fora en staatspropaganda
SKIP_DOMAINS = {"msn.com", "fok.nl", "marketscreener.com", "vietnam.vn", "rt.com", "sputnikglobe.com", "tass.com",
                "globaltimes.cn", "presstv.ir", "newsbreak.com", "ground.news", "newsnow.co.uk"}
# gekende, betrouwbare media met gratis artikels: daar volstaan 2 gemeenschappelijke woorden, anders 3
TRUSTED_DOMAINS = {
    "vrt.be", "bruzz.be", "rtbf.be", "lalibre.be", "nos.nl", "nu.nl", "rtl.be", "rtl.nl", "lavenir.net", "belganewsagency.eu",
    "brusselstimes.com", "thebulletin.be", "lesoir.be", "bnr.nl", "nporadio1.nl", "tf1info.fr", "francetvinfo.fr", "20minutes.fr",
    "ouest-france.fr", "lefigaro.fr", "liberation.fr", "rfi.fr", "france24.com", "euronews.com", "reuters.com", "apnews.com",
    "bbc.com", "bbc.co.uk", "theguardian.com", "npr.org", "dw.com", "aljazeera.com", "politico.eu", "cbc.ca", "abc.net.au",
    "yahoo.com", "aol.com", "techcrunch.com", "engadget.com", "arstechnica.com", "tweakers.net", "datanews.be",
}

LANG_HINTS = {
    "nl": set("het een van is dat niet zijn voor met ook wordt naar".split()),
    "fr": set("le la les des est une pas que pour dans sur avec".split()),
    "en": set("the and of is that to was for with on are has".split()),
    "es": set("el los las del por una para con como pero más está".split()),
}


def domain(url):
    host = urllib.parse.urlparse(url).netloc.lower().split(":")[0]
    parts = host.split(".")
    keep = 3 if len(parts) > 2 and parts[-2] in ("co", "com", "org", "net") and len(parts[-1]) == 2 else 2
    return ".".join(parts[-keep:])


def detect_lang(paras):
    words = re.findall(r"[a-zà-ÿ']+", " ".join(paras[:6]).lower())
    counts = {lang: sum(w in hints for w in words) for lang, hints in LANG_HINTS.items()}
    lang = max(counts, key=counts.get)
    return lang if counts[lang] >= 8 else None


def keywords(title, summary, idf, tokens):
    """De 3 meest typerende woorden: zeldzame woorden en namen eerst."""
    words = re.findall(r"[\wÀ-ÿ'’-]+", title)
    # namen midden in een zin van de samenvatting (geen zinsbegin)
    words += re.findall(r"(?<=[a-zà-ÿ,] )[A-ZÀ-Ý][\wÀ-ÿ-]{2,}", summary)
    scored, seen = [], set()
    for i, w in enumerate(words):
        t = next(iter(tokens(w)), None)
        if not t or len(w) < 4 or t in seen:
            continue
        seen.add(t)
        name = w[0].isupper() and i > 0
        scored.append((idf.get(t, max(idf.values(), default=1)) + (1.5 if name else 0), w.strip("'’-")))
    scored.sort(reverse=True)
    return [w for _, w in scored[:3]]


def bing(query, fetch, parse_feed):
    raw = fetch(SEARCH_URL + urllib.parse.quote(query), timeout=15)
    out = []
    for it in parse_feed(raw):
        real = urllib.parse.parse_qs(urllib.parse.urlparse(it["link"]).query).get("url", [it["link"]])[0]
        out.append({"link": real, "title": it["title"], "summary": it["summary"], "image": it["image"],
                    "published": it["published"].isoformat() if it["published"] else None})
    return out


def find_free(groups, items, ctx):
    """Geeft [(groep, gevonden artikel)] terug voor verhalen zonder vrij leesbare versie.

    ctx: dict met fetch, parse_feed, tokens, is_blocked, get_page (link -> cache-item), now
    """
    cache = json.loads(CACHE_FILE.read_text("utf-8")) if CACHE_FILE.exists() else {}
    tokens, now = ctx["tokens"], ctx["now"]

    df = {}
    for it in items:
        for t in tokens(f"{it.get('orig_title') or it['title']} {it.get('orig_summary') or it['summary']}"):
            df[t] = df.get(t, 0) + 1
    idf = {t: math.log(len(items) / c) for t, c in df.items()}

    walled = [g for g in groups if not any(it["text_orig"] for it in g) and any(it["why"] in WALLS for it in g)]
    walled.sort(key=lambda g: (len({it["source"] for it in g}), max(it["published"] for it in g)), reverse=True)

    found, searches, keep = [], 0, set()
    for g in walled:
        lead = g[0]
        key = lead["link"]
        keep.add(key)
        entry = cache.get(key)
        stale = entry and not entry["hit"] and entry["tries"] < 3 and \
            now - datetime.fromisoformat(entry["at"]) > timedelta(hours=RETRY_AFTER_H)
        if entry is None or stale:
            if searches >= MAX_SEARCHES:
                continue
            searches += 1
            entry = {"at": now.isoformat(), "tries": (entry or {}).get("tries", 0) + 1, "hit": None}
            cache[key] = entry
            try:
                entry["hit"] = search_one(g, idf, ctx)
            except Exception as e:  # zoeken mislukt: volgende keer opnieuw
                print(f"  zoeken mislukt voor '{lead['title'][:50]}': {e}")
            time.sleep(1)
        if entry["hit"]:
            found.append((g, entry["hit"]))

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({k: v for k, v in cache.items() if k in keep}, ensure_ascii=False), "utf-8")
    print(f"Vrije versies gezocht voor {searches} verhalen achter een muur; {len(found)}/{len(walled)} gevonden")
    return found


def search_one(group, idf, ctx):
    tokens, now = ctx["tokens"], ctx["now"]
    lead = group[0]
    title = lead.get("orig_title") or lead["title"]
    summary = lead.get("orig_summary") or lead["summary"]
    kws = keywords(title, summary, idf, tokens)
    if len(kws) < 2:
        return None
    kw_tokens = set().union(*(tokens(k) for k in kws))
    story_tokens = set()
    for it in group:
        story_tokens |= tokens(f"{it.get('orig_title') or it['title']} {it.get('orig_summary') or it['summary']} {it['title']} {it['summary']}")
    own_domains = {domain(it["link"]) for it in group}
    oldest = min(it["published"] for it in group) - timedelta(days=5)

    # eerst met de 3 sterkste woorden, dan breder met de 2 sterkste
    results = ctx["bing"](" ".join(kws))
    if len(kws) > 2:
        results += ctx["bing"](" ".join(kws[:2]))
    tried, seen = 0, set()
    for c in results:
        if c["link"] in seen:
            continue
        seen.add(c["link"])
        d = domain(c["link"])
        if d in own_domains or d in SKIP_DOMAINS or ctx["is_blocked"](c["link"]):
            continue
        published = datetime.fromisoformat(c["published"]) if c["published"] else now
        if published < oldest or published > now + timedelta(hours=1):
            continue
        cand = tokens(f"{c['title']} {c['summary']}")
        need = 2 if d in TRUSTED_DOMAINS else 3
        if len(cand & story_tokens) < need or len(tokens(c["title"]) & story_tokens) < 2 or not cand & kw_tokens:
            continue
        if tried >= MAX_CANDIDATES:
            break
        tried += 1
        page = ctx["get_page"](c["link"])
        lang = detect_lang(page.get("p", []))
        if page.get("p") and lang:
            return c | {"lang": lang, "domain": d, "site": page.get("site") or d, "query": " ".join(kws)}
    return None
