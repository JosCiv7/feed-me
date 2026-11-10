# Feed Me

Persoonlijke nieuwsapp: België, Brussel, tech en de wereld via lokale bronnen, zonder sensatiemedia.
Per nieuwsfeit zie je welke media erover berichten en uit welke politieke hoek ze komen, en lees je de
meest neutrale versie volledig in de app, met een korte samenvatting in bullets. Franse, Spaanse en Engelse artikels worden gratis en offline naar het Nederlands vertaald.

**Online:** https://josciv7.github.io/feed-me/ (wordt elke 30 minuten automatisch bijgewerkt door GitHub Actions)

## Op je Android installeren

Open het adres hierboven in Chrome en tik bovenaan op **Installeer app** (of tik op ⋮ en kies **App installeren**; bij
**Toevoegen aan startscherm** kies je **Installeren**, niet **Snelkoppeling maken**). Feed Me verschijnt dan tussen je apps. Je wachtwoord blijft bewaard.
Open een artikel en geef één keer je wachtwoord in (zie hieronder) om de volledige teksten te lezen.

## Wachtwoord voor de volledige artikels

De volledige teksten van andere media staan versleuteld online, zodat enkel jij ze kan lezen.
Het wachtwoord staat enkel op je pc (nooit online) en in GitHub als geheim `FEEDME_KEY`
(Settings → Secrets and variables → Actions). De app zegt nergens waar het te vinden is.
Laat Chrome het bewaren wanneer je het de eerste keer ingeeft; dan vult Chrome het voortaan zelf in.

## Zelf nieuw nieuws ophalen

GitHub slaat zijn geplande updates soms urenlang over. Is het nieuws ouder dan 20 minuten, dan start de
vernieuwknop zelf een update (± 8 minuten). Daarvoor vraagt de app één keer een GitHub-sleutel
(fine-grained token, enkel voor `feed-me`, met als enige recht *Actions: Read and write*). Die blijft enkel op je toestel.

## Starten op je pc

Dubbelklik op **Feed Me starten.bat**. Die haalt het nieuws op, leest en vertaalt de artikels en opent de app in je browser.
De eerste keer installeert hij de vertaler en downloadt hij de vertaalmodellen (± 170 MB).

## Instellingen: rubrieken

Het knopje met de schuifjes rechtsboven opent de instellingen. Je keuzes worden enkel op dat toestel bewaard.
- **Rubrieken:** elke rubriek aan of uit; met de ster krijgt een rubriek extra voorrang in "Voor jou".
- **Taal (staat uit):** Feed Me vertaalt enkel naar het Nederlands, zodat een update snel blijft. Zet je in
  `fetcher/sources.py` bij `LANGUAGES` ook `"fr"` of `"en"`, dan verschijnt in de instellingen een taalkeuze en wordt
  alles ook naar die taal vertaald (de app zelf is al vertaald). Dat kost extra vertaaltijd per update.

## Betere vertaling (optioneel, op je eigen pc)

Online gebruikt Feed Me de kleine Argos-modellen. Op je pc kan je grotere modellen installeren met
`python fetcher/get_models.py`; Feed Me gebruikt ze dan vanzelf. Gemeten op 36 zinnen in alle richtingen tussen
Nederlands, Frans en Engels (chrF, hoger = beter); een deel van die zinnen staat in `tests/vertaling/testset.json`:

| motor | kwaliteit | snelheid | gebruikt voor |
|---|---|---|---|
| Argos | 65.6 | snel | standaard (ook online) |
| OPUS-MT tc-big (± 700 MB) | 67.2 | ± 10 zinnen/s | volledige artikels |
| MADLAD-400 3B (± 3 GB) | 73.0 | ± 1.4 zinnen/s | titels en samenvattingen |

Zelf testen: `python tests/vertaling/evalueer.py`. Motor kiezen: `FEEDME_TRANSLATOR` (titels) en
`FEEDME_TRANSLATOR_TEXTS` (artikels) op `argos`, `tcbig` of `madlad`.

## Links/rechts en toon

Hoe de politieke labels en de toonanalyse werken en waartegen ze nagekeken zijn, staat in `tests/links-rechts.md`.
Testgevallen: `python -m unittest discover tests`.

## Hoe het werkt

- `fetcher/sources.py`: de bronnenlijst, politieke labels, geweerde sensatiemedia en klikaas-filters. Hier pas je alles aan.
- `fetcher/fetch_news.py`: haalt de RSS-feeds op, filtert, vertaalt, groepeert per nieuwsfeit en schrijft `app/data/news.json`.
- `fetcher/articles.py`: haalt de volledige tekst van elk artikel op. Betaal- en loginmuren worden gerespecteerd.
- `fetcher/neutral.py`: kiest per nieuwsfeit de meest neutrale versie (bron, volledige tekst, geladen woorden, opinie of niet).
- `fetcher/translate.py`: offline vertaling (Argos, of de grotere modellen als die geïnstalleerd zijn; geen account of betaling nodig).
- `fetcher/search.py`: zoekt een gratis versie van nieuws dat enkel achter een betaalmuur staat.
- `fetcher/summary.py`: maakt de korte samenvatting (de belangrijkste zinnen uit het artikel zelf).
- `fetcher/vault.py`: versleutelt de volledige teksten met je wachtwoord (`app/data/texts.bin`).
- `app/`: de app zelf (installeerbaar op Android als web-app).
