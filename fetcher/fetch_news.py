"""Haalt alle RSS-feeds op, filtert sensatie, groepeert artikels per nieuwsfeit
en schrijft app/data/news.json. Enkel standaard Python, geen installaties nodig.

Gebruik:  python fetcher/fetch_news.py
"""
import concurrent.futures
import email.utils
import html
import json
import math
import re
import time
import urllib.request
import zlib
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import translate
from sources import SOURCES, BLOCKED_DOMAINS, CLICKBAIT_PATTERNS, INTEREST_BOOST

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "app" / "data" / "news.json"
IMAGE_CACHE_FILE = ROOT / "fetcher" / "cache" / "images.json"

USER_AGENT = "Mozilla/5.0 (Feed Me persoonlijke nieuwslezer)"
MAX_AGE_HOURS = 36
MAX_OG_LOOKUPS = 250

CLICKBAIT_RE = [re.compile(p, re.I) for p in CLICKBAIT_PATTERNS]

BELGIUM_RE = re.compile(
    r"\b(belg\w*|vlaander\w*|vlaams\w*|walloni\w*|waals\w*|wallon\w*|flamand\w*|brussel\w*|bruxell\w*"
    r"|antwerp\w*|anvers|gent|gand|leuven|louvain|brugge|bruges|luik|li[eè]ge|namen|namur|charleroi"
    r"|mechelen|hasselt|kortrijk|oostende|ostende|aalst|genk|limburg|mons|bergen|tournai|doornik"
    r"|n-va|vlaams belang|vooruit|cd&v|open vld|groen|pvda|ptb|les engag[ée]s|ecolo"
    r"|de wever|federale regering|gouvernement f[ée]d[ée]ral|nmbs|sncb|de lijn|mivb|stib|zaventem)\b",
    re.I,
)
BRUSSELS_RE = re.compile(
    r"\b(brussel\w*|bruxell\w*|anderlecht|molenbeek|scha[ae]r?beek|schaerbeek|elsene|ixelles|etterbeek"
    r"|ukkel|uccle|jette|vorst|sint-gillis|saint-gilles|laken|laeken|evere|oudergem|auderghem"
    r"|watermaal|sint-joost|saint-josse|ganshoren|koekelberg|mivb|stib)\b",
    re.I,
)
EU_RE = re.compile(r"\b(europese (commissie|unie|raad)|eu-|commission europ|union europ|navo|nato)\b", re.I)
TECH_ACRONYM_RE = re.compile(r"\b(AI|IA)\b")
TECH_RE = re.compile(
    r"\b(artifici[eë]le intelligentie|intelligence artificielle|chatgpt|openai|anthropic|nvidia"
    r"|apple|google|microsoft|meta|amazon|tesla|smartphone|iphone|android|chip\w*|software|cyber\w*"
    r"|hack\w*|startup|start-up|tech\w*|robot\w*|algoritme|datacenter|5g|elektrische auto)\b",
    re.I,
)

STOPWORDS = set("""
de het een en van in op te dat die is voor met zijn er aan niet om als ook bij of uit maar nog naar door over dan
wordt worden werd was zal zou kan heeft hebben had wat wie waar hoe nu al meer dit deze na tot geen men we ze hij
zij je jij u ons onze hun haar zich toch wel zo nieuwe nieuw jaar jaren dag vandaag gisteren morgen
live liveblog volg hier alle updates moet goed groot tegen ooit nodig mijn hebt blijft
direct suivez live
le la les un une des du de et en au aux dans sur pour par avec est sont pas plus ce cette ces qui que se sa son ses
il elle ils elles nous vous leur leurs mais ou donc ont été être fait après avant selon entre
the a an and of in on to for with is are was were be been by at from as that this it its his her their they he she
not but or after over new says said will would can could has have had more than into about up out who what
""".split())


def fetch(url, limit=None, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept-Language": "nl-BE,nl;q=0.9,fr;q=0.8,en;q=0.7"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read(limit) if limit else resp.read()
        charset = resp.headers.get_content_charset() or "utf-8"
    return data.decode(charset, "ignore")


def clean_text(s):
    if not s:
        return ""
    s = re.sub(r"<!\[CDATA\[(.*?)\]\]>", r"\1", s, flags=re.S)
    s = html.unescape(s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def tag(block, *names):
    for name in names:
        m = re.search(rf"<{name}(?:\s[^>]*)?>(.*?)</{name}>", block, re.S | re.I)
        if m and m.group(1).strip():
            return m.group(1)
    return ""


def find_link(block):
    m = re.search(r"<link>\s*(?:<!\[CDATA\[)?\s*(https?://[^<\]\s]+)", block, re.I)
    if m:
        return html.unescape(m.group(1))
    for m in re.finditer(r"<link\b([^>]*)/?>", block, re.I):
        attrs = m.group(1)
        href = re.search(r'href="([^"]+)"', attrs)
        rel = re.search(r'rel="([^"]+)"', attrs)
        if href and (not rel or rel.group(1) == "alternate"):
            return html.unescape(href.group(1))
    m = re.search(r'<guid[^>]*isPermaLink="true"[^>]*>(.*?)</guid>', block, re.S | re.I)
    return clean_text(m.group(1)) if m else ""


def find_image(block):
    patterns = [
        r'<media:content[^>]+url="([^"]+)"[^>]*(?:medium="image"|type="image)',
        r'<media:content[^>]+(?:medium="image"|type="image[^"]*")[^>]*url="([^"]+)"',
        r'<media:thumbnail[^>]+url="([^"]+)"',
        r'<enclosure[^>]+url="([^"]+)"[^>]*type="image',
        r'<enclosure[^>]+type="image[^"]*"[^>]*url="([^"]+)"',
        r'<media:content[^>]+url="([^"]+\.(?:jpe?g|png|webp)[^"]*)"',
    ]
    for p in patterns:
        m = re.search(p, block, re.I)
        if m:
            return html.unescape(m.group(1))
    m = re.search(r'<img[^>]+src="([^"]+)"', html.unescape(block), re.I)
    return m.group(1) if m else ""


def parse_date(s):
    s = clean_text(s)
    if not s:
        return None
    try:
        d = email.utils.parsedate_to_datetime(s)
    except (TypeError, ValueError):
        try:
            d = datetime.fromisoformat(s.replace("Z", "+00:00"))
        except ValueError:
            return None
    if d.tzinfo is None:
        d = d.replace(tzinfo=timezone.utc)
    return d.astimezone(timezone.utc)


def parse_feed(raw):
    blocks = re.findall(r"<item[\s>].*?</item>", raw, re.S | re.I) or re.findall(r"<entry[\s>].*?</entry>", raw, re.S | re.I)
    items = []
    for b in blocks:
        title = clean_text(tag(b, "title"))
        link = find_link(b)
        if not title or not link:
            continue
        desc = clean_text(tag(b, "description", "summary", "content:encoded", "content"))
        desc = re.sub(r"\s*The post .* appeared first on .*$", "", desc)  # WordPress-voetnoot
        items.append({
            "title": title,
            "link": link,
            "summary": desc[:280] + ("…" if len(desc) > 280 else ""),
            "image": find_image(b),
            "published": parse_date(tag(b, "pubDate", "dc:date", "published", "updated")),
        })
    return items


def fetch_source(src):
    for attempt in range(2):
        try:
            items = parse_feed(fetch(src["url"]))
            return src, items, None
        except Exception as e:  # netwerkfout: één keer opnieuw proberen, dan overslaan
            err = f"{type(e).__name__}: {e}"
            if "403" in err or "429" in err:
                break
            time.sleep(1.5)
    return src, [], err


def is_blocked(link):
    host = urlparse(link).netloc.lower()
    return any(host == d or host.endswith("." + d) for d in BLOCKED_DOMAINS)


def is_clickbait(title):
    return any(r.search(title) for r in CLICKBAIT_RE)


def og_image(url):
    try:
        page = fetch(url, limit=200_000, timeout=12)
    except Exception:
        return ""
    for p in (r'<meta[^>]+property="og:image"[^>]+content="([^"]+)"', r'<meta[^>]+content="([^"]+)"[^>]+property="og:image"',
              r'<meta[^>]+name="twitter:image"[^>]+content="([^"]+)"'):
        m = re.search(p, page, re.I)
        if m:
            return html.unescape(m.group(1))
    return ""


def tokens(text):
    words = re.findall(r"[a-zà-ÿ0-9][a-zà-ÿ0-9\-']+", text.lower())
    return {w.strip("-'") for w in words if len(w) > 2 and w not in STOPWORDS}


def sections_for(item, src):
    text = f"{item['title']} {item['summary']}"
    secs = set()
    if src["kind"] == "tech" or TECH_RE.search(item["title"]) or TECH_ACRONYM_RE.search(item["title"]):
        secs.add("tech")
    if src["country"] == "BE":
        # Brussel enkel als het in de titel staat ("Van Brussel tot Rome…" in een intro telt niet)
        if src["kind"] == "brussel" or (BRUSSELS_RE.search(item["title"]) and not EU_RE.search(text)):
            secs.add("brussel")
        if src["kind"] in ("be", "brussel") and (src["kind"] == "brussel" or BELGIUM_RE.search(text)):
            secs.add("belgie")
        elif src["kind"] == "be":
            secs.add("wereld")
    elif src["kind"] == "world":
        secs.add("wereld")
    return secs


def cluster(items):
    """Groepeer artikels over hetzelfde nieuwsfeit (zelfde taal, gelijkaardige woorden)."""
    docs = [tokens(f"{it['title']} {it['summary'][:160]}") for it in items]
    df = {}
    for d in docs:
        for t in d:
            df[t] = df.get(t, 0) + 1
    n = len(docs)
    idf = {t: math.log(n / c) for t, c in df.items()}
    weights = [{t: idf[t] for t in d} for d in docs]
    norms = [math.sqrt(sum(v * v for v in w.values())) or 1 for w in weights]

    index = {}
    for i, d in enumerate(docs):
        for t in d:
            if df[t] <= 25:
                index.setdefault(t, []).append(i)

    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for i in range(n):
        candidates = {j for t in docs[i] if t in index for j in index[t] if j > i}
        for j in candidates:
            if items[i]["source"] == items[j]["source"]:
                continue
            shared = docs[i] & docs[j]
            if len(shared) < 3:
                continue
            sim = sum(weights[i][t] * weights[j][t] for t in shared) / (norms[i] * norms[j])
            if sim >= 0.38:
                parent[find(i)] = find(j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(items[i])
    return list(groups.values())


def build_story(group, src_by_id, now):
    # Hoofdartikel: liefst Nederlandstalig, met foto, meest recent
    group.sort(key=lambda it: (src_by_id[it["source"]]["lang"] == "nl", bool(it["image"]), it["published"]), reverse=True)
    lead = group[0]
    sections = set().union(*(it["sections"] for it in group))
    leans = {}
    for it in group:
        lean = src_by_id[it["source"]]["lean"]
        if lean:
            leans[lean] = leans.get(lean, 0) + 1
    left = leans.get("L", 0) + leans.get("CL", 0)
    right = leans.get("R", 0) + leans.get("CR", 0)
    labeled = sum(leans.values())
    blindspot = None
    if labeled >= 3 and left / labeled >= 0.8:
        blindspot = "vooral links"
    elif labeled >= 3 and right / labeled >= 0.8:
        blindspot = "vooral rechts"

    newest = max(it["published"] for it in group)
    age_h = (now - newest).total_seconds() / 3600
    n_sources = len({it["source"] for it in group})
    boost = max(INTEREST_BOOST.get(s, 1.0) for s in sections) if sections else 1.0
    score = (1 + 1.5 * math.log2(1 + n_sources)) * math.exp(-age_h / 14) * boost

    return {
        "id": zlib.crc32(lead["link"].encode()),
        "title": lead["title"],
        "orig_title": lead.get("orig_title"),
        "summary": lead["summary"],
        "image": next((it["image"] for it in group if it["image"]), ""),
        "link": lead["link"],
        "source": lead["source"],
        "lang": src_by_id[lead["source"]]["lang"],
        "published": newest.isoformat(),
        "sections": sorted(sections),
        # rubriek-label volgt het hoofdartikel, niet de som van alle bronnen
        "kicker": next((s for s in ("brussel", "belgie", "tech", "wereld") if s in lead["sections"]), None),
        "score": round(score, 4),
        "leans": leans,
        "blindspot": blindspot,
        "articles": [
            {"source": it["source"], "title": it["title"], "orig_title": it.get("orig_title"), "link": it["link"],
             "published": it["published"].isoformat()}
            for it in sorted(group, key=lambda it: it["published"], reverse=True)
        ],
    }


def main():
    now = datetime.now(timezone.utc)
    src_by_id = {s["id"]: s for s in SOURCES}
    image_cache = json.loads(IMAGE_CACHE_FILE.read_text("utf-8")) if IMAGE_CACHE_FILE.exists() else {}

    all_items, status = [], {}
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        for src, items, err in ex.map(fetch_source, SOURCES):
            kept = 0
            for it in items:
                if not it["published"]:
                    it["published"] = now
                if (now - it["published"]).total_seconds() > src.get("max_age_h", MAX_AGE_HOURS) * 3600:
                    continue
                if is_blocked(it["link"]) or is_clickbait(it["title"]):
                    continue
                it["source"] = src["id"]
                it["sections"] = sections_for(it, src)
                if not it["sections"]:
                    continue
                all_items.append(it)
                kept += 1
            status[src["id"]] = {"ok": err is None, "items": kept, "error": err}
            print(f"{'OK ' if err is None else 'ERR'} {src['name']:26} {kept:3} artikels" + (f"  ({err[:70]})" if err else ""))

    # Dubbele links eruit
    seen, items = set(), []
    for it in sorted(all_items, key=lambda it: it["published"], reverse=True):
        if it["link"] not in seen:
            seen.add(it["link"])
            items.append(it)

    # Frans en Engels vertalen naar het Nederlands (offline, gratis)
    if translate.AVAILABLE:
        t0 = time.time()
        tr = translate.Translator()
        for lang in translate.ROUTES:
            todo = [it for it in items if src_by_id[it["source"]]["lang"] == lang]
            titles = tr.translate([it["title"] for it in todo], lang)
            summaries = tr.translate([it["summary"] for it in todo], lang)
            for it, t, s in zip(todo, titles, summaries):
                it["orig_title"] = it["title"]
                it["title"], it["summary"] = t, s
        tr.save()
        print(f"Vertaald in {time.time() - t0:.0f}s")
    else:
        print("Vertalen overgeslagen: installeer eerst  pip install -r requirements.txt")

    # Ontbrekende foto's opzoeken via de og:image van het artikel (met cache)
    missing = [it for it in items if not it["image"] and it["link"] not in image_cache][:MAX_OG_LOOKUPS]
    with concurrent.futures.ThreadPoolExecutor(16) as ex:
        for it, img in zip(missing, ex.map(lambda it: og_image(it["link"]), missing)):
            image_cache[it["link"]] = img
    for it in items:
        if not it["image"]:
            it["image"] = image_cache.get(it["link"], "")

    stories = [build_story(g, src_by_id, now) for g in cluster(items)]
    stories.sort(key=lambda s: s["score"], reverse=True)

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(json.dumps({
        "generated": now.isoformat(),
        "sources": [{k: s[k] for k in ("id", "name", "lang", "country", "kind", "lean")} | status.get(s["id"], {}) for s in SOURCES],
        "rules": {"blocked": BLOCKED_DOMAINS},
        "stories": stories,
    }, ensure_ascii=False), "utf-8")

    keep_links = {it["link"] for it in items}
    IMAGE_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    IMAGE_CACHE_FILE.write_text(json.dumps({k: v for k, v in image_cache.items() if k in keep_links}), "utf-8")

    multi = sum(1 for s in stories if len(s["articles"]) > 1)
    print(f"\n{len(items)} artikels -> {len(stories)} verhalen ({multi} met meerdere bronnen) -> {OUT_FILE}")


if __name__ == "__main__":
    main()
