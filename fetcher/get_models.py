"""Installeert de grotere vertaalmodellen in fetcher/models (eenmalig, optioneel, ± 4 GB).

Gebruik:  pip install torch transformers huggingface_hub ctranslate2 sentencepiece protobuf
          python fetcher/get_models.py            (of: python fetcher/get_models.py tcbig   /   madlad)
- tcbig:  OPUS-MT tc-big van de Universiteit van Helsinki (CC-BY 4.0), omgezet naar CTranslate2 (int8)
- madlad: MADLAD-400 3B van Google (Apache 2.0), kant-en-klaar in CTranslate2-formaat
Daarna gebruikt translate.py ze vanzelf (zie BEST en LONG in translate.py).
"""
import subprocess
import sys
from pathlib import Path

MODELS = Path(__file__).resolve().parent / "models"
want = sys.argv[1:] or ["tcbig", "madlad"]

if "tcbig" in want:
    for name in ("fr-en", "en-fr", "gmw-gmw"):
        out = MODELS / f"tcbig_{name}"
        if not (out / "model.bin").exists():
            subprocess.run(["ct2-transformers-converter", "--model", f"Helsinki-NLP/opus-mt-tc-big-{name}", "--output_dir", str(out),
                            "--quantization", "int8", "--copy_files", "source.spm", "target.spm", "--force"], check=True)
        print("ok", out)

if "madlad" in want:
    from huggingface_hub import snapshot_download
    out = MODELS / "madlad400_3b"
    snapshot_download("Nextcloud-AI/madlad400-3b-mt-ct2-int8", local_dir=str(out), allow_patterns=["*.json", "model.bin", "spiece.model"])
    print("ok", out)
