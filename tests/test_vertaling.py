"""Testgevallen voor de hulpjes rond de vertaling en het ophalen (geen vertaalmodel nodig).

Gebruik:  python -m unittest discover tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "fetcher"))
import fetch_news  # noqa: E402
import search  # noqa: E402
import translate  # noqa: E402


class Leftovers(unittest.TestCase):
    def test_onvertaald_eerste_woord(self):
        self.assertEqual(translate.leftovers("Cae una banda que robó artículos", "Cae een band die items gestolen"), 1)

    def test_onvertaald_werkwoord_midden_in_de_zin(self):
        self.assertEqual(translate.leftovers("Un tren de mercancías descarrila en Madrid", "Een goederentrein descarrila in Madrid"), 1)

    def test_namen_tellen_niet_mee(self):
        self.assertEqual(translate.leftovers("Un tren descarrila en Madrid y Ávila", "Een trein ontspoort in Madrid en Ávila"), 0)

    def test_goede_vertaling(self):
        self.assertEqual(translate.leftovers("Muere un motorista sin casco", "Een motorrijder zonder helm sterft"), 0)


class Glossary(unittest.TestCase):
    def test_rassemblement_national(self):
        out = translate.apply_glossary("Le Rassemblement national veut couper l'aide", "De National Rally wil de hulp verminderen", "fr")
        self.assertEqual(out, "Het Rassemblement National wil de hulp verminderen")

    def test_hexagone(self):
        out = translate.apply_glossary("L'Hexagone affiche une croissance faible", "Hexagon heeft een zwakke groei", "fr")
        self.assertEqual(out, "Frankrijk heeft een zwakke groei")

    def test_guardia_civil_midden_in_de_zin(self):
        out = translate.apply_glossary("Detenidos por la Guardia Civil", "Aangehouden door de burgerwacht", "es")
        self.assertEqual(out, "Aangehouden door de Guardia Civil")

    def test_enkel_als_het_in_de_bron_staat(self):
        # een echte burgerwacht in een Franse tekst blijft een burgerwacht
        self.assertEqual(translate.apply_glossary("Une milice citoyenne", "Een burgerwacht", "fr"), "Een burgerwacht")

    def test_kiev(self):
        self.assertEqual(translate.apply_glossary("Zelenskyy says Kyiv holds", "Zelenskyy zegt dat Kyiv standhoudt", "en"),
                         "Zelensky zegt dat Kiev standhoudt")


class Titels(unittest.TestCase):
    def test_punt_enkel_zonder_leesteken(self):
        self.assertFalse(translate.END_RE.search("Muere un motorista en Eivissa (Baleares)"))
        self.assertTrue(translate.END_RE.search("Waarom duurt het zo lang?"))

    def test_toegevoegde_punt_weer_weg(self):
        self.assertEqual(translate.ADDED_DOT_RE.sub("", "Een motorrijder sterft.", count=1), "Een motorrijder sterft")
        self.assertEqual(translate.ADDED_DOT_RE.sub("", '"We hebben het opgelost."', count=1), '"We hebben het opgelost"')

    def test_hapering_weggepoetst(self):
        self.assertEqual(translate.tidy("EU" + "." * 90), "EU…")


class Dateline(unittest.TestCase):
    def test_persbureau(self):
        strip = lambda s: fetch_news.DATELINE_RE.sub("", s)
        self.assertEqual(strip("SEOUL, Nov. 14 (Yonhap) -- The ICT ministry said"), "The ICT ministry said")
        self.assertEqual(strip("(ANSA) - ROME, NOV 14 - Italy said"), "Italy said")

    def test_gewone_zin_blijft(self):
        strip = lambda s: fetch_news.DATELINE_RE.sub("", s)
        self.assertEqual(strip("De regering zei, na 14 dagen - iets"), "De regering zei, na 14 dagen - iets")
        self.assertEqual(strip("Madrid is groot"), "Madrid is groot")


class Veiligheid(unittest.TestCase):
    def test_enkel_gewone_weblinks_uit_een_feed(self):
        feed = ("<rss><item><title>Goed</title><link>https://example.org/a</link></item>"
                "<item><title>Fout</title><guid isPermaLink=\"true\">javascript:alert(1)</guid></item>"
                "<item><title>Ook fout</title><link href=\"data:text/html,x\"/></item></rss>")
        self.assertEqual([it["title"] for it in fetch_news.parse_feed(feed)], ["Goed"])

    def test_wachtwoordbestand_en_tussenstand_komen_nooit_online(self):
        root = Path(__file__).resolve().parent.parent
        ignored = (root / ".gitignore").read_text("utf-8").split()
        self.assertIn("fetcher/cache/", ignored)
        self.assertIn("wachtwoord.txt", ignored)  # "Feed Me wachtwoord.txt"
        # niets uit fetcher/ wordt gepubliceerd: de tussenstand staat buiten de map app/
        self.assertNotIn("app", fetch_news.STATE_FILE.parts)


class Zoeken(unittest.TestCase):
    def test_sensatie_en_onbekende_sites_niet_betrouwbaar(self):
        for d in ("thesun.ie", "gbnews.com", "afrik-foot.com", "yahoo.com", "msn.com"):
            self.assertNotIn(d, search.TRUSTED_DOMAINS)

    def test_geweerde_media_staan_niet_in_de_betrouwbare_lijst(self):
        self.assertFalse([d for d in search.TRUSTED_DOMAINS if fetch_news.is_blocked(f"https://www.{d}/x")])

    def test_domein(self):
        self.assertEqual(search.domain("https://news.sky.com/story/x"), "sky.com")
        self.assertEqual(search.domain("https://www.bbc.co.uk/news/x"), "bbc.co.uk")


class Europa(unittest.TestCase):
    def test_politico_europe_komt_in_europa(self):
        src = {"kind": "world", "country": "EU"}
        item = {"title": "Finland rejects demand", "summary": "", "link": "https://www.politico.eu/article/x/"}
        self.assertEqual(fetch_news.sections_for(item, src), {"wereld", "europa"})

    def test_trefwoorden(self):
        for title in ("Europees Parlement stemt over migratiepact", "Vijf EU-landen willen terugkeerhub", "Eurocommissaris op het matje"):
            item = {"title": title, "summary": "", "sections": set()}
            fetch_news.add_topics(item)
            self.assertIn("europa", item["sections"], title)

    def test_geen_europa(self):
        item = {"title": "Trein ontspoort in Madrid", "summary": "", "sections": set()}
        fetch_news.add_topics(item)
        self.assertNotIn("europa", item["sections"])


if __name__ == "__main__":
    unittest.main()
