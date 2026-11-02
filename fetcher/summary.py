"""Korte samenvatting in bullets, gemaakt uit het volledige artikel (gratis, zonder AI-dienst).

Werkwijze ("extractief"): we kiezen de zinnen die het best weergeven waar het artikel over gaat
en zetten ze in de volgorde van het artikel. Er wordt dus niets bijgeschreven of verzonnen;
elke bullet is een zin uit het artikel zelf.
- woorden die vaak terugkomen in het artikel en in de titel wegen zwaarder
- zinnen vooraan in het artikel krijgen een kleine voorsprong (nieuws zet het belangrijkste eerst)
- zinnen die zonder context niet te begrijpen zijn ("Dat zei hij ook.") scoren lager
- zinnen die te veel op een al gekozen zin lijken, worden overgeslagen
Aantal bullets: 5 tot 10, afhankelijk van de lengte. Korte artikels krijgen geen samenvatting.
"""
import math
import re

MIN_SENTENCES = 10
STOP = set("""
de het een en van in op te dat die is voor met zijn er aan niet om als ook bij of uit maar nog naar door over dan
wordt worden werd was zal zou kan heeft hebben had wat wie waar hoe nu al meer dit deze na tot geen men we ze hij
zij je jij u ons onze hun haar zich toch wel zo zei zegt volgens
""".split())
# zinnen die naar iets eerder verwijzen en los niet goed leesbaar zijn
CONTEXT_START = re.compile(r"^(hij|zij|ze|het|dat|dit|die|deze|daarom|daardoor|daarnaast|bovendien|maar|en|ook|toch|dan|er|net|zo)\b", re.I)
SPLIT = re.compile(r"(?<=[.!?])[\"”’']?\s+(?=[\"“‘'(]?[A-ZÀ-Ý0-9])")
ABBREV = re.compile(r"\b(bv|bijv|o\.a|dhr|mevr|mr|dr|prof|nr|st|ca|resp|vs|mio|mld)\.$", re.I)


def sentences(paras):
    out = []
    for p in paras:
        if len(p) < 90 and not re.search(r"[.!?:;\"”'’)]$", p):  # tussentitel
            continue
        p = re.sub(r"^[-•–*]\s+", "", p)  # opsommingstekens van de site zelf
        buf = ""
        for part in SPLIT.split(p):
            buf = f"{buf} {part}".strip() if buf else part
            if ABBREV.search(buf):
                continue
            out.append(buf)
            buf = ""
        if buf:
            out.append(buf)
    return out


def words(s):
    return [w[:6] for w in re.findall(r"[a-zà-ÿ0-9]+", s.lower()) if len(w) > 2 and w not in STOP]


def summarize(paras, title=""):
    sents = sentences(paras)
    if len(sents) < MIN_SENTENCES:
        return []
    total_words = sum(len(s.split()) for s in sents)
    n = max(5, min(10, round(total_words / 110), len(sents) // 2))

    toks = [words(s) for s in sents]
    tf = {}
    for t in toks:
        for w in set(t):
            tf[w] = tf.get(w, 0) + 1
    title_w = set(words(title))

    scored = []
    for i, (s, t) in enumerate(zip(sents, toks)):
        n_words = len(s.split())
        if not t or n_words < 7:
            continue
        score = sum(tf[w] for w in set(t) if tf[w] > 1) / math.sqrt(len(set(t)))
        score += 2.0 * len(title_w & set(t)) / (len(title_w) or 1)
        score += max(0.0, 1.5 - i * 0.15)       # voorsprong voor het begin
        if n_words > 45:
            score *= 0.6
        if CONTEXT_START.match(s):
            score *= 0.7
        if s.rstrip("”\"'’").endswith("?"):
            score *= 0.5
        if s[0] in "\"“‘'«":  # los citaat: minder informatief dan een feitelijke zin
            score *= 0.75
        scored.append((score, i))
    scored.sort(reverse=True)

    chosen = []
    for score, i in scored:
        if len(chosen) >= n:
            break
        ti = set(toks[i])
        if any(len(ti & set(toks[j])) / (min(len(ti), len(toks[j])) or 1) > 0.4 for j in chosen):
            continue
        chosen.append(i)
    return [sents[i] for i in sorted(chosen)]
