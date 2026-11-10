"""Testgevallen voor de analyse van toon, opinie, blinde vlek en politieke labels (fetcher/neutral.py, fetcher/sources.py).

Gebruik:  python -m unittest discover tests
Elk geval komt uit echt nieuws of uit een fout die we in de echte data vonden (10 november 2026).
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "fetcher"))
import neutral  # noqa: E402
import sources  # noqa: E402

CENTRE = {"lean": "C"}
CL = {"lean": "CL"}
LEFT = {"lean": "L"}
NONE = {"lean": None}
BODY = ["Een gewone, feitelijke paragraaf over de resultaten van het bedrijf in het derde kwartaal. " * 6] * 5


def art(title, link="https://example.be/nieuws/artikel-123", paras=BODY):
    return {"title": title, "link": link, "text_orig": paras}


class GeladenWoorden(unittest.TestCase):
    def test_echte_geladen_woorden_tellen(self):
        for title in ("Schandalig: bedrijf ontslaat 600 mensen", "Un scandale chez le fournisseur", "Minister slams 'outrageous' plan"):
            self.assertTrue(neutral.assess(art(title), CENTRE)["loaded"], title)

    def test_beschrijvende_woorden_tellen_niet(self):
        # vals alarm uit de echte data: in cybernieuws is "propaganda" een beschrijving, geen oordeel
        cases = [
            "Iraanse hackers verspreiden propaganda via gehackte koelsystemen",
            "La propagande russe cible les PME belges",
            "The real problem lies in legacy SAP systems",
            "La rage de dents du ministre",
            "Thuiswerken is een rage bij IT-bedrijven",
        ]
        for title in cases:
            self.assertEqual(neutral.assess(art(title), CENTRE)["loaded"], [], title)

    def test_geladen_titel_scoort_lager(self):
        calm = neutral.assess(art("Bedrijf ontslaat 600 mensen"), CENTRE)["neutral"]
        loaded = neutral.assess(art("Schandalig: bedrijf ontslaat 600 mensen"), CENTRE)["neutral"]
        self.assertLess(loaded, calm)

    def test_hoofdletters_en_uitroeptekens_tellen(self):
        calm = neutral.assess(art("Orange Belgium verhoogt prijzen"), CENTRE)["neutral"]
        shouty = neutral.assess(art("ORANGE verhoogt OPNIEUW prijzen!"), CENTRE)["neutral"]
        self.assertLess(shouty, calm)

    def test_afkortingen_zijn_geen_roepen(self):
        a = neutral.assess(art("NAVO en VRT over NIS2"), CENTRE)["neutral"]
        b = neutral.assess(art("Navo en VRT over regels"), CENTRE)["neutral"]
        self.assertGreaterEqual(a, b - 0.6)  # NIS2 telt hoogstens als één hoofdletterwoord


class Opinie(unittest.TestCase):
    def test_opinie_via_webadres(self):
        for link in ("https://www.standaard.be/opinie/abc", "https://www.lesoir.be/edito/123", "https://www.theregister.com/comment/x"):
            self.assertTrue(neutral.assess(art("Titel", link), CENTRE)["opinion"], link)

    def test_opinie_via_titel(self):
        # gemist in de echte data: L'Echo zet het genre enkel in de titel
        for title in ("Édito | Quand Jensen Huang est devenu humain, trop humain", "Opinie: Europa moet durven investeren",
                      "Column - De CIO als dirigent", "Carte blanche : sauver nos PME", "Analyse: wat NIS2 echt vraagt"):
            self.assertTrue(neutral.assess(art(title, "https://www.lecho.be/r/t/1/id/1"), CENTRE)["opinion"], title)

    def test_rubriek_in_titel_is_geen_opinie(self):
        # "France:", "Media:", "FWB:" zijn rubrieken of plaatsen, geen opinie
        for title in ("France: Éric Zemmour annonce sa candidature", "Media: Microsoft lobbyt tegen verbod",
                      "FWB: syndicats et gouvernement renouent le dialogue", "Inge Geerdens: \"Medewerkers moeten kunnen ruziemaken\""):
            self.assertFalse(neutral.assess(art(title), CENTRE)["opinion"], title)

    def test_opinie_scoort_lager_dan_nieuws(self):
        news = neutral.assess(art("Europa investeert in chips"), CENTRE)["neutral"]
        op = neutral.assess(art("Opinie: Europa investeert in chips"), CENTRE)["neutral"]
        self.assertLess(op, news)

    def test_liveblog(self):
        self.assertTrue(neutral.assess(art("Staking", "https://www.vrt.be/vrtnws/nl/live/staking"), CENTRE)["live"])
        self.assertFalse(neutral.assess(art("Delivery", "https://example.com/delivery-plan"), CENTRE)["live"])


class NeutraalsteVersie(unittest.TestCase):
    def test_centrum_voor_links(self):
        self.assertGreater(neutral.assess(art("X"), CENTRE)["neutral"], neutral.assess(art("X"), CL)["neutral"])
        self.assertGreater(neutral.assess(art("X"), CL)["neutral"], neutral.assess(art("X"), LEFT)["neutral"])

    def test_volledige_tekst_weegt_zwaarder_dan_label(self):
        # liever een vakbron die je kan lezen dan een centrumbron achter een betaalmuur
        open_trade = neutral.assess(art("X"), NONE)["neutral"]
        walled_centre = neutral.assess(art("X", paras=[]), CENTRE)["neutral"]
        self.assertGreater(open_trade, walled_centre)

    def test_redenen_als_codes(self):
        a = {"text": True, "loaded": [], "found": None}
        self.assertEqual(neutral.reasons(a, CENTRE, 2), [["lean_C", 0], ["text", 0], ["loaded", 0], ["others", 2]])


class BlindeVlek(unittest.TestCase):
    def test_bijna_enkel_links(self):
        self.assertEqual(neutral.blindspot({"CL": 2, "L": 1}), "left")
        self.assertEqual(neutral.blindspot({"CL": 4, "C": 1}), "left")  # 80%

    def test_bijna_enkel_rechts(self):
        self.assertEqual(neutral.blindspot({"CR": 3}), "right")

    def test_gemengd_is_geen_blinde_vlek(self):
        self.assertIsNone(neutral.blindspot({"CR": 2, "C": 1}))  # 67% < 80%
        self.assertIsNone(neutral.blindspot({"CL": 1, "CR": 1, "C": 1}))

    def test_te_weinig_bronnen(self):
        self.assertIsNone(neutral.blindspot({"CR": 2}))
        self.assertIsNone(neutral.blindspot({}))

    def test_centrum_telt_als_tegengewicht(self):
        self.assertIsNone(neutral.blindspot({"CL": 3, "C": 2}))  # 60%


class Labels(unittest.TestCase):
    by_id = {s["id"]: s for s in sources.SOURCES}

    def test_geldige_labels(self):
        for s in sources.SOURCES:
            self.assertIn(s["lean"], (None, "L", "CL", "C", "CR", "R"), s["id"])

    def test_openbare_omroepen_gelijk(self):
        self.assertEqual(self.by_id["vrt"]["lean"], self.by_id["rtbf"]["lean"])

    def test_zelfde_extern_profiel_zelfde_label(self):
        # Media Bias/Fact Check: beide "Least Biased", licht rechts van het midden
        self.assertEqual(self.by_id["standaard"]["lean"], self.by_id["lalibre"]["lean"])

    def test_zusterkranten_gelijk(self):
        self.assertEqual(self.by_id["tijd"]["lean"], self.by_id["lecho"]["lean"])

    def test_techpers_zonder_label(self):
        # politieke labels gaan over het nieuwslandschap; techbronnen krijgen er geen
        for s in sources.SOURCES:
            if s["kind"] == "tech":
                self.assertIsNone(s["lean"], s["id"])

    def test_evenwicht_in_belgische_bronnen(self):
        # geen kant mag de Belgische bronnen domineren, anders worden blinde vlekken scheef
        leans = [s["lean"] for s in sources.SOURCES if s["kind"] in ("be", "brussel") and s["lean"]]
        left = sum(l in ("L", "CL") for l in leans)
        right = sum(l in ("R", "CR") for l in leans)
        self.assertLessEqual(abs(left - right), 2, (left, right))

    def test_spaanse_bronnen_beide_kanten(self):
        leans = {s["lean"] for s in sources.SOURCES if s["kind"] == "spanje"}
        self.assertTrue(leans & {"L", "CL"} and leans & {"R", "CR"}, leans)


if __name__ == "__main__":
    unittest.main()
