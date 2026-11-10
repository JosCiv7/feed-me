# Links/rechts en toon in Feed Me: hoe het werkt en wat we nagekeken hebben

Nagekeken op 10 november 2026. Testgevallen: `tests/test_neutral.py` (24 tests, `python -m unittest discover tests`).

## Wat Feed Me wél en níet doet

- **Geen links/rechts per artikel.** Feed Me beoordeelt niet of een artikel zelf links of rechts is. Dat kan een
  eenvoudig programma niet betrouwbaar, en een fout label op een artikel is erger dan geen label.
- **Een label per medium** (redactielijn): L, CL, C, CR, R. Voor Belgische en Spaanse bronnen (en Politico);
  techbronnen en de meeste buitenlandse bronnen krijgen geen label.
- **Toon per artikel:** geladen woorden ("schandalig", "slams"), hoofdletters, uitroeptekens, opinie of liveblog.
- **Meest neutrale versie:** per verhaal de versie met het beste totaal (centrumbron, volledige tekst, rustige toon, geen opinie).
- **Blinde vlek:** een verhaal dat minstens 3 gelabelde bronnen heeft en voor 80% of meer van één kant komt.

## Labels nagekeken tegen externe bronnen

| Medium | Was | Nu | Waarom |
|---|---|---|---|
| VRT NWS | C | C | Media Bias/Fact Check (MBFC): *Least Biased* (2024); meest vertrouwd in Vlaanderen (Reuters DNR) |
| De Standaard | C | C | MBFC: *Least Biased*, licht rechts (2025); Eurotopics: liberaal-conservatief |
| De Morgen | CL | CL | MBFC: *Left-Center* (2025); Eurotopics: links |
| De Tijd / L'Echo | CR | CR | Eurotopics: liberale zakenkrant; zusterkranten krijgen hetzelfde label |
| RTBF | CL | **C** | Geen extern onderzoek dat CL staaft, enkel kritiek van politici; openbare omroepen krijgen hetzelfde label als VRT |
| La Libre | CR | **C** | MBFC: *Least Biased*, "minimaal rechts" (2025), zelfde profiel als De Standaard |
| Knack | C | C (open vraag) | Eurotopics noemt Knack uitgesproken links; maar één bron, dus nog niet aangepast |
| Bruzz | C | C | Geen externe beoordeling; Bruzz is wettelijk tot onpartijdigheid verplicht |
| MO*, 't Pallieterke, Spaanse bronnen | ongewijzigd | ongewijzigd | Niet opnieuw nagekeken |

Bronnen: mediabiasfactcheck.com (pagina's per medium), eurotopics.net (mediaprofielen), Reuters Institute Digital News
Report Belgium 2017–2026. De DNR publiceert voor België geen politieke ligging van het publiek per merk.

## Fouten gevonden in de echte data (en opgelost)

1. **"propaganda" telde 28 keer als geladen woord**. In cybernieuws is het een beschrijving ("Iraanse propaganda").
   Ook Engels "lies" ("the problem lies in") en Frans "rage" (ook: hondsdolheid) gaven vals alarm. Uit de lijst gehaald.
2. **Opinie gemist als het genre enkel in de titel staat**, zoals bij L'Echo ("Édito | …"). Nu ook herkend in de titel
   (Opinie:, Column -, Édito |, Carte blanche :, Analyse: …), zonder rubrieken als "France:" of "Media:" mee te tellen.

## Beperkingen (eerlijk)

- **De blinde vlek vraagt minstens 3 gelabelde bronnen.** In Feed Me (veel algemene Belgische en Spaanse bronnen) komt
  dat vaker voor dan in vakpers-feeds; de regel zelf (80% van één kant) is getest in `tests/test_neutral.py`.
- **Labels gaan over het medium, niet over elk artikel.** Een opiniestuk in De Tijd zegt iets anders dan een kort Belga-bericht erin.
- **Externe beoordelingen zijn zelf inschattingen.** MBFC baseert zich vooral op titels en opiniestukken; Eurotopics beschrijft eerder.
