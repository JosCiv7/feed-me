"""Gratis, offline vertaling (Nederlands, Frans, Engels) met de open-source modellen van Argos Translate.

Werkt volledig op je eigen computer (of op GitHub), zonder account of API-sleutel.
Nodig: pip install -r requirements.txt   (ctranslate2 + sentencepiece)
Zonder rechtstreeks model gaat het via het Engels (bv. fr -> en -> nl, nl -> en -> fr).
"""
import io
import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODELS_DIR = ROOT / "models"
CACHE_FILE = ROOT / "cache" / "translations.json"
INDEX_URL = "https://raw.githubusercontent.com/argosopentech/argospm-index/main/index.json"
USER_AGENT = "FeedMe/1.0 (+https://github.com/JosCiv7/feed-me)"  # de standaard Python-naam wordt geweigerd
ARGOS_LOCAL = Path.home() / ".local" / "share" / "argos-translate" / "packages"

# de nieuwste es->en (1.9) gebruikt een ander woordsplitsformaat; versie 1.0 werkt met sentencepiece zoals de rest
PINNED = {("es", "en"): "https://argos-net.com/v1/translate-es_en-1_0.argosmodel"}

# welke stappen nodig zijn per brontaal naar het Nederlands (de taal waarin Feed Me intern groepeert en thema's zoekt)
ROUTES = {"en": [("en", "nl")], "fr": [("fr", "en"), ("en", "nl")], "es": [("es", "en"), ("en", "nl")]}
# de talen waarin je Feed Me kan lezen, en hoe je er vanuit elke brontaal geraakt
LANGS = ("nl", "fr", "en")
PATHS = {
    ("en", "nl"): [("en", "nl")], ("fr", "nl"): [("fr", "en"), ("en", "nl")], ("es", "nl"): [("es", "en"), ("en", "nl")],
    ("nl", "en"): [("nl", "en")], ("fr", "en"): [("fr", "en")], ("es", "en"): [("es", "en")],
    ("nl", "fr"): [("nl", "en"), ("en", "fr")], ("en", "fr"): [("en", "fr")], ("es", "fr"): [("es", "en"), ("en", "fr")],
}

try:
    import ctranslate2
    import sentencepiece
    AVAILABLE = True
except ImportError:
    AVAILABLE = False


def _model_dir(src, tgt):
    return MODELS_DIR / f"{src}_{tgt}"


def _install(src, tgt):
    """Zorg dat het model src->tgt in fetcher/models staat (kopie van Argos of download)."""
    dest = _model_dir(src, tgt)
    if (dest / "model" / "model.bin").exists():
        return
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    local = next(iter(sorted(ARGOS_LOCAL.glob(f"translate-{src}_{tgt}-*"))), None) if ARGOS_LOCAL.exists() else None
    if local:
        shutil.copytree(local / "model", dest / "model", dirs_exist_ok=True)
        shutil.copy(local / "sentencepiece.model", dest / "sentencepiece.model")
        return
    print(f"Vertaalmodel {src}->{tgt} downloaden…")
    url = PINNED.get((src, tgt))
    if not url:
        index = json.loads(urllib.request.urlopen(INDEX_URL, timeout=60).read())
        url = next(p for p in index if p["from_code"] == src and p["to_code"] == tgt)["links"][0]
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    data = urllib.request.urlopen(req, timeout=600).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            parts = Path(name).parts[1:]  # bovenste map van het zip-bestand overslaan
            if not parts or name.endswith("/"):
                continue
            if parts[0] == "model" or parts[-1] == "sentencepiece.model":
                target = dest.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))


def tidy(text):
    """Herstel de typische haperingen van het vertaalmodel (bv. "EU......" met tientallen puntjes)."""
    text = re.sub(r"\.{4,}", "…", text)
    text = re.sub(r"(\W)\1{3,}", r"\1", text)  # andere eindeloos herhaalde leestekens
    return re.sub(r"\s{2,}", " ", text).strip()


# --- vertaalmotoren ---
# argos  = de kleine Argos-modellen (± 100 MB per richting, snel, matige kwaliteit)
# tcbig  = OPUS-MT "tc-big" van de Universiteit van Helsinki (± 250 MB per richting, CC-BY 4.0)
# madlad = MADLAD-400 3B van Google (± 3 GB, één model voor alle richtingen, Apache 2.0, traagst)
# Getest op tests/vertaling/testset.json (chrF, hoger = beter): argos 65.6 · tcbig 67.2 · madlad 73.0.
# madlad is het best maar ± 10x trager, dus standaard:
# - titels en samenvattingen (kort, wat je eerst ziet): de beste motor die geïnstalleerd is  (FEEDME_TRANSLATOR)
# - volledige artikels (lang, duizenden zinnen):        tcbig als die er is                  (FEEDME_TRANSLATOR_TEXTS)
BEST = ("madlad", "tcbig", "argos")
LONG = ("tcbig", "madlad", "argos")
SENTENCE_RE = re.compile(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý\"“'‘«])")


def split_sentences(texts):
    """Zin per zin vertalen geeft betere resultaten dan een hele alinea in één keer."""
    pieces, owners = [], []
    for i, t in enumerate(texts):
        for s in SENTENCE_RE.split(t or ""):
            if s.strip():
                pieces.append(s.strip())
                owners.append(i)
    return pieces, owners


def join_sentences(texts, owners, results):
    out = [[] for _ in texts]
    for i, r in zip(owners, results):
        out[i].append(r)
    return [" ".join(parts) for parts in out]


class ArgosEngine:
    name = "argos"

    def __init__(self):
        self.models = {}

    @staticmethod
    def installed():
        return (MODELS_DIR / "en_nl" / "model" / "model.bin").exists() or True  # downloadt zelf wat ontbreekt

    def _model(self, src, tgt):
        if (src, tgt) not in self.models:
            _install(src, tgt)
            d = _model_dir(src, tgt)
            self.models[(src, tgt)] = (
                ctranslate2.Translator(str(d / "model"), device="cpu", inter_threads=1, intra_threads=0),
                sentencepiece.SentencePieceProcessor(model_file=str(d / "sentencepiece.model")),
            )
        return self.models[(src, tgt)]

    def _step(self, sents, src, tgt):
        model, sp = self._model(src, tgt)
        results = model.translate_batch([sp.encode(s, out_type=str) for s in sents], beam_size=2, max_batch_size=32, max_decoding_length=200)
        return ["".join(r.hypotheses[0]).replace("▁", " ").strip() for r in results]

    def translate(self, texts, src, tgt):
        pieces, owners = split_sentences(texts)
        for a, b in PATHS[(src, tgt)]:
            pieces = self._step(pieces, a, b) if pieces else pieces
        return join_sentences(texts, owners, pieces)


class TcBigEngine:
    """OPUS-MT tc-big: fr<->en en en<->nl rechtstreeks (nl<->en via het West-Germaanse model), nl<->fr via het Engels."""
    name = "tcbig"
    MODELS = {("fr", "en"): ("tcbig_fr-en", None), ("en", "fr"): ("tcbig_en-fr", None),
              ("nl", "en"): ("tcbig_gmw-gmw", ">>eng<<"), ("en", "nl"): ("tcbig_gmw-gmw", ">>nld<<")}

    def __init__(self):
        self.loaded = {}

    @classmethod
    def installed(cls):
        return all((MODELS_DIR / d / "model.bin").exists() for d, _ in cls.MODELS.values())

    def _model(self, folder):
        if folder not in self.loaded:
            d = MODELS_DIR / folder
            self.loaded[folder] = (
                ctranslate2.Translator(str(d), device="cpu", inter_threads=1, intra_threads=0),
                sentencepiece.SentencePieceProcessor(model_file=str(d / "source.spm")),
                sentencepiece.SentencePieceProcessor(model_file=str(d / "target.spm")),
            )
        return self.loaded[folder]

    def _step(self, sents, src, tgt):
        folder, prefix = self.MODELS[(src, tgt)]
        model, sp_src, sp_tgt = self._model(folder)
        batch = [([prefix] if prefix else []) + sp_src.encode(s, out_type=str) + ["</s>"] for s in sents]
        results = model.translate_batch(batch, beam_size=4, max_batch_size=16, max_decoding_length=256)
        return [sp_tgt.decode_pieces([t for t in r.hypotheses[0] if t not in ("</s>", "<pad>")]).strip() for r in results]

    def translate(self, texts, src, tgt):
        pieces, owners = split_sentences(texts)
        if pieces:
            if (src, tgt) in self.MODELS:
                steps = [(src, tgt)]
            elif src == "en" or tgt == "en":
                steps = PATHS[(src, tgt)]
            else:  # nl<->fr, es->nl, es->fr: via het Engels
                steps = [(src, "en"), ("en", tgt)]
            for a, b in steps:
                # geen tc-big-model voor deze stap (bv. es->en): dan het kleine Argos-model
                pieces = self._step(pieces, a, b) if (a, b) in self.MODELS else self._argos()._step(pieces, a, b)
        return join_sentences(texts, owners, pieces)

    def _argos(self):
        if not hasattr(self, "argos"):
            self.argos = ArgosEngine()
        return self.argos


class MadladEngine:
    """MADLAD-400 3B: één meertalig model, vertaalt nl<->fr rechtstreeks (geen omweg via het Engels)."""
    name = "madlad"
    FOLDER = "madlad400_3b"

    def __init__(self):
        self.model = None

    @classmethod
    def installed(cls):
        return (MODELS_DIR / cls.FOLDER / "model.bin").exists()

    def translate(self, texts, src, tgt):
        if self.model is None:
            d = MODELS_DIR / self.FOLDER
            self.model = ctranslate2.Translator(str(d), device="cpu", compute_type="int8", inter_threads=1, intra_threads=0)
            self.sp = sentencepiece.SentencePieceProcessor(model_file=str(d / "spiece.model"))
        pieces, owners = split_sentences(texts)
        if pieces:
            batch = [self.sp.encode(f"<2{tgt}> {s}", out_type=str) + ["</s>"] for s in pieces]
            results = self.model.translate_batch(batch, beam_size=2, max_batch_size=8, max_decoding_length=256, repetition_penalty=1.1)
            pieces = [self.sp.decode_pieces([t for t in r.hypotheses[0] if t not in ("</s>", "<pad>")]).strip() for r in results]
        return join_sentences(texts, owners, pieces)


ENGINES = {"argos": ArgosEngine, "tcbig": TcBigEngine, "madlad": MadladEngine}


def make_engine(name=None, kind="short"):
    import os
    env = os.environ.get("FEEDME_TRANSLATOR_TEXTS" if kind == "long" else "FEEDME_TRANSLATOR")
    name = name or env or next(n for n in (LONG if kind == "long" else BEST) if ENGINES[n].installed())
    return ENGINES[name]()


class Translator:
    def __init__(self, engine=None):
        self.cache = json.loads(CACHE_FILE.read_text("utf-8")) if CACHE_FILE.exists() else {}
        self.used = set()
        self.engines = {"short": make_engine(engine, "short")}
        long = make_engine(engine, "long")
        self.engines["long"] = self.engines["short"] if long.name == self.engines["short"].name else long
        print(f"Vertaalmotor: {self.engines['short'].name} (titels), {self.engines['long'].name} (artikels)")

    def _key(self, t, lang, target, kind="short"):
        # argos naar het Nederlands: het oude formaat, zodat de bestaande cache blijft werken; andere motoren apart
        name = self.engines[kind].name
        key = f"{lang}|{t}" if target == "nl" else f"{lang}>{target}|{t}"
        return key if name == "argos" else f"{name}:{key}"

    def has(self, texts, lang, target="nl", kind="short"):
        """Zijn al deze teksten al eens vertaald (dus gratis uit de cache)?"""
        return all(not t or self._key(t, lang, target, kind) in self.cache for t in texts)

    def translate(self, texts, lang, target="nl", kind="short"):
        """Vertaal teksten van `lang` naar `target` (met cache). kind="long" = volledige artikels (snellere motor)."""
        if lang == target:
            return list(texts)
        keys = [self._key(t, lang, target, kind) for t in texts]
        todo = sorted({t for t, k in zip(texts, keys) if t and k not in self.cache})
        if todo:
            result = self.engines[kind].translate(todo, lang, target)
            for t, r in zip(todo, result):
                self.cache[self._key(t, lang, target, kind)] = r
        self.used.update(keys)
        return [tidy(self.cache.get(k, t)) if t else t for t, k in zip(texts, keys)]

    def save(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({k: v for k, v in self.cache.items() if k in self.used}, ensure_ascii=False), "utf-8")
