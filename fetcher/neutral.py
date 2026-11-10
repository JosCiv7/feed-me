"""Kiest per nieuwsfeit de meest neutrale versie om in de app te tonen.

Dit is een eenvoudige, controleerbare puntentelling (geen AI):
- politieke positie van de bron (centrum scoort het best)
- volledige tekst beschikbaar, zodat je het in de app kan lezen
- geladen of sensationele woorden en uitroeptekens (in de originele taal geteld)
- opiniestukken en liveblogs scoren lager dan gewone nieuwsberichten
De redenen worden mee opgeslagen, zodat de app kan tonen waarom een versie gekozen werd.
"""
import re

LOADED_WORDS = """
schandalig schandaal schande schokkend shock choquerend woedend woede razend furieus drama dramatisch chaos chaotisch
catastrofe catastrofaal rampzalig hallucinant onvoorstelbaar ongezien ongelooflijk absurd belachelijk waanzin waanzinnig
krankzinnig horror gruwel gruwelijk verbijsterend bizar hysterie hetze heksenjacht afrekening vernietigend keihard sneer
uithaal veeg ophef rel relletje sensationeel idioot leugen leugens liegt woke wokisme clown fiasco blunder
scandaleux scandale choc choquant furieux colère drame dramatique chaotique catastrophique désastre désastreux
incroyable inouï ridicule délirant horreur horrible effroyable stupéfiant hystérie fustige étrille dézingue cinglant
tollé mensonge mensonges fiasco
outrage outrageous shocking furious fury slams slammed blasts blasted rips destroys chaotic catastrophic disastrous
unbelievable insane ridiculous horrific stunning bombshell explosive hysteria scathing brutal firestorm uproar liar
meltdown humiliating humiliation disgrace disgraceful
""".split()
# Bewust NIET in de lijst (getest op echt nieuws, zie tests/test_neutral.py):
# "propaganda"/"propagande" (in cybernieuws een beschrijving: "Iraanse propaganda"), Engels "lies" ("the problem lies in"),
# Frans "rage" (ook: hondsdolheid) en "rage" in het Nederlands ("een rage").
LOADED_RE = re.compile(r"\b(" + "|".join(map(re.escape, LOADED_WORDS)) + r")\b", re.I)

OPINION_RE = re.compile(r"/(opinie|opinion|opinions|column|columns|commentary|comment|edito|editorial|debat|blogs?|analyse|analysis)/", re.I)
# sommige sites (L'Echo, De Tijd) zetten het genre enkel in de titel: "Édito | ...", "Opinie: ...", "Column - ..."
OPINION_TITLE_RE = re.compile(
    r"^\s*(opinie|column|commentaar|analyse|[eé]dito|[eé]ditorial|editorial|carte blanche|chronique|tribune|opinion|analysis|comment|"
    r"lezersbrief|brief van de dag|l'édito|het commentaar|de column)\s*[|:–—-]", re.I)
LIVE_RE = re.compile(r"/(live|liveblog|direct)[/-]|[-/]live[-/]", re.I)
CAPS_RE = re.compile(r"\b[A-ZÀ-Ý]{4,}\b")

LEAN_POINTS = {"C": 3, "CL": 2, "CR": 2, "L": 0, "R": 0, None: 2}
LEAN_TEXT = {"C": "centrumbron", "CL": "centrum-links", "CR": "centrum-rechts", "L": "linkse bron", "R": "rechtse bron"}


def assess(item, src):
    """Bereken toon en neutraliteitsscore van één artikel (op de originele tekst)."""
    title = item.get("orig_title") or item["title"]
    paras = item.get("text_orig") or []
    body = " ".join(paras)
    words = len(body.split())

    found = [m.lower() for m in LOADED_RE.findall(f"{title} {body}")]
    in_title = len(LOADED_RE.findall(title))
    exclaim = title.count("!") + body.count("!")
    caps = len([w for w in CAPS_RE.findall(title) if w not in ("NAVO", "NATO", "VRT", "RTBF", "BBC", "EU", "VS", "USA")])
    per_1000 = len(found) / max(words, 300) * 1000

    score = LEAN_POINTS.get(src["lean"], 2)
    score += 4 if paras else 0
    score -= min(4, per_1000 / 2) + in_title + 0.5 * exclaim + 0.5 * caps
    opinion = bool(OPINION_RE.search(item["link"]) or OPINION_TITLE_RE.search(title))
    live = bool(LIVE_RE.search(item["link"]))
    score -= 5 if opinion else 0
    score -= 2 if live else 0
    score += min(1, words / 600)

    return {
        "neutral": round(score, 2),
        "loaded": sorted(set(found))[:6],
        "opinion": opinion,
        "live": live,
        "words": words,
    }


def blindspot(leans):
    """"left" of "right" als een verhaal bijna enkel (>= 80%) door één kant gebracht wordt, door minstens 3 gelabelde bronnen."""
    left = leans.get("L", 0) + leans.get("CL", 0)
    right = leans.get("R", 0) + leans.get("CR", 0)
    labeled = sum(leans.values())
    if labeled >= 3 and left / labeled >= 0.8:
        return "left"
    if labeled >= 3 and right / labeled >= 0.8:
        return "right"
    return None


def reasons(article, src, others):
    """Waarom deze versie gekozen werd, als codes [code, getal]; de app zet ze om in de gekozen taal."""
    out = []
    if article.get("found"):
        out.append(["found", 0])
    if src["lean"]:
        out.append(["lean_" + src["lean"], 0])
    if article["text"]:
        out.append(["text", 0])
    out.append(["loaded", len(article["loaded"])])
    if others:
        out.append(["others", others])
    return out
