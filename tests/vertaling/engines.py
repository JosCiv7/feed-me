"""Motoren voor de vertaaltest: dezelfde code als de app (fetcher/translate.py), maar zonder cache."""
import translate


class Plain:
    def __init__(self, name):
        self.engine = translate.make_engine(name)

    def translate(self, texts, src, tgt):
        return [translate.tidy(t) for t in self.engine.translate(texts, src, tgt)]


def load(name):
    return Plain(name)
