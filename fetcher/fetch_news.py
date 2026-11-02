"""Haalt alle RSS-feeds op, filtert sensatie, haalt de volledige tekst op, groepeert artikels per nieuwsfeit,
kiest per nieuwsfeit de meest neutrale versie en schrijft app/data/news.json (+ versleuteld texts.bin).

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

import articles
import neutral
import search
import summary
import translate
import vault
from sources import SOURCES, BLOCKED_DOMAINS, CLICKBAIT_PATTERNS, INTEREST_BOOST

ROOT = Path(__file__).resolve().parent.parent
OUT_FILE = ROOT / "app" / "data" / "news.json"
TEXTS_FILE = ROOT / "app" / "data" / "texts.bin"

USER_AGENT = "Mozilla/5.0 (Feed Me persoonlijke nieuwslezer)"
MAX_AGE_HOURS = 36
MAX_ITEMS_PER_SOURCE = 40   # zodat één drukke bron de rest niet overspoelt
MAX_PAGE_FETCHES = 500      # nieuwe artikelpagina's per run
TRANSLATE_SECONDS = 300     # tijd voor het vertalen van volledige teksten per run
SIM_THRESHOLD = 0.3         # hoe gelijkaardig twee titels moeten zijn om hetzelfde nieuwsfeit te zijn

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


def tokens(text):
    words = re.findall(r"[a-zà-ÿ0-9][a-zà-ÿ0-9\-']+", text.lower())
    # enkel de eerste 6 letters: zo zijn "supermarket" en "supermarkets" (en "cyberattack"/"cyberaanval") hetzelfde woord
    return {w.strip("-'")[:6] for w in words if len(w) > 2 and w not in STOPWORDS}


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


def similar_pairs(items, docs):
    """Paren artikels (van verschillende bronnen) met genoeg gelijkaardige, zeldzame woorden."""
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

    for i in range(n):
        candidates = {j for t in docs[i] if t in index for j in index[t] if j > i}
        for j in candidates:
            if items[i]["source"] == items[j]["source"]:
                continue
            shared = docs[i] & docs[j]
            if len(shared) < 3:
                continue
            sim = sum(weights[i][t] * weights[j][t] for t in shared) / (norms[i] * norms[j])
            if sim >= SIM_THRESHOLD:
                yield i, j


def cluster(items):
    """Groepeer artikels over hetzelfde nieuwsfeit.

    Twee keer vergelijken: op de vertaalde (Nederlandse) titels, zodat talen elkaar vinden,
    en op de originele titels, omdat twee Engelse bronnen elkaar in het Engels beter herkennen
    dan na twee verschillende automatische vertalingen.
    """
    translated = [tokens(f"{it['title']} {it['summary'][:160]}") for it in items]
    original = [tokens(f"{it.get('orig_title') or it['title']} {(it.get('orig_summary') or it['summary'])[:160]}") for it in items]
    n = len(items)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for docs in (translated, original):
        for i, j in similar_pairs(items, docs):
            parent[find(i)] = find(j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(items[i])
    return list(groups.values())


def build_story(group, src_by_id, now):
    # Getoonde versie: de meest neutrale (zie neutral.py); bij gelijke stand die met foto, dan de nieuwste
    group.sort(key=lambda it: (it["neutral"], bool(it["image"]), it["published"]), reverse=True)
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

    arts = [{
        "id": it["id"], "source": it["source"], "title": it["title"], "orig_title": it.get("orig_title"),
        "summary": it["summary"], "image": it["image"], "link": it["link"], "published": it["published"].isoformat(),
        "text": bool(it["text_orig"]), "why": it["why"], "words": it["words"], "loaded": it["loaded"],
        "opinion": it["opinion"], "live": it["live"], "neutral": it["neutral"], "found": it.get("found"),
    } for it in group]  # eerste = gekozen versie, daarna de rest van meest naar minst neutraal

    return {
        "id": lead["id"],
        "title": lead["title"],
        "orig_title": lead.get("orig_title"),
        "summary": lead["summary"],
        "image": lead["image"] or next((it["image"] for it in group if it["image"]), ""),
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
        "why_pick": neutral.reasons(arts[0], src_by_id[lead["source"]], len(group) - 1),
        "articles": arts,
    }


def main():
    now = datetime.now(timezone.utc)
    src_by_id = {s["id"]: s for s in SOURCES}

    all_items, status = [], {}
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        for src, items, err in ex.map(fetch_source, SOURCES):
            kept = 0
            items.sort(key=lambda it: it["published"] or now, reverse=True)
            for it in items:
                if kept >= src.get("max_items", MAX_ITEMS_PER_SOURCE):
                    break
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

    # Titels en samenvattingen in het Frans en Engels vertalen naar het Nederlands (offline, gratis)
    tr = None
    if translate.AVAILABLE:
        t0 = time.time()
        tr = translate.Translator()
        for lang in translate.ROUTES:
            todo = [it for it in items if src_by_id[it["source"]]["lang"] == lang]
            titles = tr.translate([it["title"] for it in todo], lang)
            summaries = tr.translate([it["summary"] for it in todo], lang)
            for it, t, s in zip(todo, titles, summaries):
                it["orig_title"], it["orig_summary"] = it["title"], it["summary"]
                it["title"], it["summary"] = t, s
        print(f"Titels vertaald in {time.time() - t0:.0f}s")
    else:
        print("Vertalen overgeslagen: installeer eerst  pip install -r requirements.txt")

    # Volledige tekst + foto van elk artikel ophalen (één keer per artikel, daarna uit de cache)
    t0 = time.time()
    page_cache = articles.load_cache()
    todo = [it for it in items if it["link"] not in page_cache
            or page_cache[it["link"]].get("retry") and page_cache[it["link"]].get("tries", 1) < 3][:MAX_PAGE_FETCHES]
    with concurrent.futures.ThreadPoolExecutor(12) as ex:
        for it, entry in zip(todo, ex.map(lambda it: articles.get(it["link"], fetch), todo)):
            entry["tries"] = page_cache.get(it["link"], {}).get("tries", 0) + 1
            page_cache[it["link"]] = entry

    def prepare(it):
        entry = page_cache.get(it["link"], {})
        it["id"] = zlib.crc32(it["link"].encode())
        it["text_orig"] = articles.trim_head(entry.get("p", []), it.get("orig_title") or it["title"])
        it["why"] = entry.get("why") if it["link"] in page_cache else "nog niet opgehaald"
        if not it["image"]:
            it["image"] = entry.get("img", "")
        it.update(neutral.assess(it, src_by_id[it["source"]]))

    for it in items:
        prepare(it)
    with_text = sum(1 for it in items if it["text_orig"])
    print(f"{len(todo)} artikelpagina's opgehaald in {time.time() - t0:.0f}s; {with_text}/{len(items)} met volledige tekst")

    groups = cluster(items)

    # Nieuws dat enkel achter een betaalmuur staat: een gratis versie bij een andere bron zoeken
    def get_page(link):
        if link not in page_cache:
            page_cache[link] = articles.get(link, fetch) | {"tries": 1}
        return page_cache[link]

    source_by_domain = {search.domain(s["url"]): s for s in SOURCES}
    web_sources = {}
    ctx = {"tokens": tokens, "now": now, "is_blocked": is_blocked, "get_page": get_page,
           "bing": lambda q: search.bing(q, fetch, parse_feed)}
    for group, c in search.find_free(groups, items, ctx):
        src = source_by_domain.get(c["domain"])
        if not src:
            src = web_sources.setdefault(c["domain"], {
                "id": f"web:{c['domain']}", "name": c["site"][:40], "lang": c["lang"], "country": "",
                "kind": "web", "lean": None, "ok": True, "items": 0, "error": None})
            src["items"] += 1
            src_by_id[src["id"]] = src
        it = {"title": c["title"], "link": c["link"], "summary": c["summary"], "image": c["image"],
              "published": datetime.fromisoformat(c["published"]) if c["published"] else now,
              "source": src["id"], "sections": set(group[0]["sections"]), "found": c["query"]}
        if tr and src["lang"] in translate.ROUTES:
            it["orig_title"], it["orig_summary"] = it["title"], it["summary"]
            it["title"], it["summary"] = tr.translate([it["title"], it["summary"]], src["lang"])
        prepare(it)
        group.append(it)
        items.append(it)

    stories = [build_story(g, src_by_id, now) for g in groups]
    stories.sort(key=lambda s: s["score"], reverse=True)

    # Volledige teksten vertalen: belangrijkste verhalen eerst, binnen een tijdslimiet (de rest volgt bij een volgende run)
    by_id = {it["id"]: it for it in items}
    texts, pending = {}, 0
    t0 = time.time()
    for story in stories:
        for a in story["articles"]:
            it = by_id[a["id"]]
            if not it["text_orig"]:
                continue
            lang = src_by_id[it["source"]]["lang"]
            entry = {"p": it["text_orig"]}
            if lang in translate.ROUTES and tr:
                if tr.has(it["text_orig"], lang) or time.time() - t0 < TRANSLATE_SECONDS:
                    entry = {"p": tr.translate(it["text_orig"], lang), "o": it["text_orig"]}
                else:
                    entry["untranslated"] = True
                    pending += 1
            if not entry.get("untranslated"):
                entry["s"] = summary.summarize(entry["p"], it["title"])
            texts[str(a["id"])] = entry
    if tr:
        tr.save()
        print(f"Volledige teksten vertaald in {time.time() - t0:.0f}s" + (f" ({pending} volgen bij de volgende update)" if pending else ""))

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    sealed = vault.seal(texts, TEXTS_FILE)
    if not sealed:
        TEXTS_FILE.unlink(missing_ok=True)
        print("Volledige teksten NIET opgeslagen: geen wachtwoord (FEEDME_KEY of 'Feed Me wachtwoord.txt') of pakket 'cryptography' ontbreekt")

    OUT_FILE.write_text(json.dumps({
        "generated": now.isoformat(),
        "texts": sealed,
        "sources": [{k: s[k] for k in ("id", "name", "lang", "country", "kind", "lean")} | status.get(s["id"], {}) for s in SOURCES]
                   + list(web_sources.values()),
        "rules": {"blocked": BLOCKED_DOMAINS},
        "stories": stories,
    }, ensure_ascii=False), "utf-8")

    articles.save_cache(page_cache, {it["link"] for it in items})

    multi = sum(1 for s in stories if len(s["articles"]) > 1)
    print(f"\n{len(items)} artikels -> {len(stories)} verhalen ({multi} met meerdere bronnen) -> {OUT_FILE}")


if __name__ == "__main__":
    main()
