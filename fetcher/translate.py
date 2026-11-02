"""Gratis, offline vertaling naar het Nederlands met de open-source modellen van Argos Translate.

Werkt volledig op je eigen computer (of op GitHub), zonder account of API-sleutel.
Nodig: pip install -r requirements.txt   (ctranslate2 + sentencepiece)
Frans gaat via het Engels naar het Nederlands (fr -> en -> nl).
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
ARGOS_LOCAL = Path.home() / ".local" / "share" / "argos-translate" / "packages"

# welke stappen nodig zijn per brontaal
ROUTES = {"en": [("en", "nl")], "fr": [("fr", "en"), ("en", "nl")]}

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
    index = json.loads(urllib.request.urlopen(INDEX_URL, timeout=60).read())
    entry = next(p for p in index if p["from_code"] == src and p["to_code"] == tgt)
    data = urllib.request.urlopen(entry["links"][0], timeout=600).read()
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        for name in z.namelist():
            parts = Path(name).parts[1:]  # bovenste map van het zip-bestand overslaan
            if not parts or name.endswith("/"):
                continue
            if parts[0] == "model" or parts[-1] == "sentencepiece.model":
                target = dest.joinpath(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(z.read(name))


class Translator:
    def __init__(self):
        self.cache = json.loads(CACHE_FILE.read_text("utf-8")) if CACHE_FILE.exists() else {}
        self.used = set()
        self.models = {}

    def _model(self, src, tgt):
        if (src, tgt) not in self.models:
            _install(src, tgt)
            d = _model_dir(src, tgt)
            self.models[(src, tgt)] = (
                ctranslate2.Translator(str(d / "model"), device="cpu", inter_threads=1, intra_threads=0),
                sentencepiece.SentencePieceProcessor(model_file=str(d / "sentencepiece.model")),
            )
        return self.models[(src, tgt)]

    def _step(self, texts, src, tgt):
        model, sp = self._model(src, tgt)
        # zin per zin vertalen geeft betere resultaten dan een hele alinea in één keer
        pieces, owners = [], []
        for i, t in enumerate(texts):
            for s in re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý\"“'‘«])", t):
                if s.strip():
                    pieces.append(sp.encode(s, out_type=str))
                    owners.append(i)
        results = model.translate_batch(pieces, beam_size=2, max_batch_size=32, max_decoding_length=200)
        out = [[] for _ in texts]
        for i, r in zip(owners, results):
            out[i].append("".join(r.hypotheses[0]).replace("▁", " ").strip())
        return [" ".join(parts) for parts in out]

    def translate(self, texts, lang):
        """Vertaal een lijst teksten van `lang` naar Nederlands (met cache)."""
        keys = [f"{lang}|{t}" for t in texts]
        todo = sorted({t for t, k in zip(texts, keys) if t and k not in self.cache})
        if todo:
            result = todo
            for src, tgt in ROUTES[lang]:
                result = self._step(result, src, tgt)
            for t, r in zip(todo, result):
                self.cache[f"{lang}|{t}"] = r
        self.used.update(keys)
        return [self.cache.get(k, t) if t else t for t, k in zip(texts, keys)]

    def save(self):
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps({k: v for k, v in self.cache.items() if k in self.used}, ensure_ascii=False), "utf-8")
