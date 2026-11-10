"""Vergelijkt vertaalmotoren op de testset (tests/vertaling/testset.json).

Gebruik:  python tests/vertaling/evalueer.py [motor ...]      (motoren: argos, tcbig, madlad; standaard alle)
Meet per motor en per richting:
- chrF: overeenkomst met de handmatige referentievertaling (0-100, hoger = beter)
- namen: hoeveel namen en termen (Orange Belgium, NIS2, SAP, ...) onvertaald behouden blijven
- tijd: seconden voor de hele testset
Schrijft ook alle vertalingen naar tests/vertaling/resultaten.md om zelf na te lezen.
"""
import json
import re
import sys
import time
from pathlib import Path

import sacrebleu

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "fetcher"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import translate  # noqa: E402  (dezelfde motorcode als de app)

HERE = Path(__file__).resolve().parent
TESTSET = json.loads((HERE / "testset.json").read_text("utf-8"))["items"]
DIRECTIONS = [(s, t) for s in ("nl", "fr", "en") for t in ("nl", "fr", "en") if s != t]


def evaluate(name, engine):
    rows, scores = [], {}
    t0 = time.time()
    for src, tgt in DIRECTIONS:
        items = [it for it in TESTSET if it["src"] == src and tgt in it]
        if not items:
            continue
        hyps = engine.translate([it["text"] for it in items], src, tgt)
        refs = [it[tgt] for it in items]
        chrf = sacrebleu.corpus_chrf(hyps, [refs]).score
        names = [(n, h) for it, h in zip(items, hyps) for n in it["names"]]
        kept = sum(1 for n, h in names if n.lower() in h.lower())
        scores[f"{src}>{tgt}"] = (chrf, kept, len(names))
        rows += [(f"{src}>{tgt}", it["text"], h, r) for it, h, r in zip(items, hyps, refs)]
    return scores, time.time() - t0, rows


def main():
    import engines
    wanted = sys.argv[1:] or ["argos", "tcbig", "madlad"]
    results, all_rows = {}, {}
    for name in wanted:
        if not translate.ENGINES[name].installed():
            print(f"\n== {name}: niet geïnstalleerd, overgeslagen (zie fetcher/get_models.py)")
            continue
        print(f"\n== {name}")
        engine = engines.load(name)
        scores, secs, rows = evaluate(name, engine)
        results[name] = (scores, secs)
        all_rows[name] = rows
        for d, (c, k, n) in scores.items():
            print(f"  {d}: chrF {c:5.1f}   namen {k}/{n}")
        avg = sum(c for c, _, _ in scores.values()) / len(scores)
        kept = sum(k for _, k, _ in scores.values()), sum(n for _, _, n in scores.values())
        print(f"  gemiddeld chrF {avg:.1f} · namen {kept[0]}/{kept[1]} · {secs:.0f}s")

    # overzicht + alle vertalingen om na te lezen
    out = ["# Vertaaltest Feed Me", "", "chrF (0-100, hoger = beter) per richting; tussen haakjes: behouden namen.", ""]
    dirs = [f"{s}>{t}" for s, t in DIRECTIONS]
    out.append("| motor | " + " | ".join(dirs) + " | gemiddeld | tijd |")
    out.append("|---" * (len(dirs) + 3) + "|")
    for name, (scores, secs) in results.items():
        cells = [f"{scores[d][0]:.1f} ({scores[d][1]}/{scores[d][2]})" if d in scores else "-" for d in dirs]
        avg = sum(c for c, _, _ in scores.values()) / len(scores)
        out.append(f"| {name} | " + " | ".join(cells) + f" | **{avg:.1f}** | {secs:.0f}s |")
    for name, rows in all_rows.items():
        out += ["", f"## {name}", ""]
        for d, src, hyp, ref in rows:
            out += [f"- **{d}** {src}", f"  - {name}: {hyp}", f"  - referentie: {ref}"]
    (HERE / "resultaten.md").write_text("\n".join(out) + "\n", "utf-8")
    print(f"\nAlles staat in {HERE / 'resultaten.md'}")


if __name__ == "__main__":
    main()
