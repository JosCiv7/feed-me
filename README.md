# Feed Me

Persoonlijke nieuwsapp: België, Brussel, tech en de wereld via lokale bronnen, zonder sensatiemedia.
Per nieuwsfeit zie je welke media erover berichten en uit welke politieke hoek ze komen, en lees je de
meest neutrale versie volledig in de app. Franse en Engelse artikels worden gratis en offline naar het Nederlands vertaald.

**Online:** https://josciv7.github.io/feed-me/ (wordt elke 30 minuten automatisch bijgewerkt door GitHub Actions)

## Op je Android installeren

Open het adres hierboven in Chrome, tik op ⋮ en kies **App installeren** (of **Toevoegen aan startscherm**).
Open een artikel en geef één keer je wachtwoord in (zie hieronder) om de volledige teksten te lezen.

## Wachtwoord voor de volledige artikels

De volledige teksten van andere media staan versleuteld online, zodat enkel jij ze kan lezen.
Het wachtwoord staat in **Feed Me wachtwoord.txt** (enkel op je pc, wordt nooit online gezet) en in GitHub
als geheim `FEEDME_KEY` (Settings → Secrets and variables → Actions).

## Starten op je pc

Dubbelklik op **Feed Me starten.bat**. Die haalt het nieuws op, leest en vertaalt de artikels en opent de app in je browser.
De eerste keer installeert hij de vertaler en downloadt hij de vertaalmodellen (± 170 MB).

## Hoe het werkt

- `fetcher/sources.py`: de bronnenlijst, politieke labels, geweerde sensatiemedia en klikaas-filters. Hier pas je alles aan.
- `fetcher/fetch_news.py`: haalt de RSS-feeds op, filtert, vertaalt, groepeert per nieuwsfeit en schrijft `app/data/news.json`.
- `fetcher/articles.py`: haalt de volledige tekst van elk artikel op. Betaal- en loginmuren worden gerespecteerd.
- `fetcher/neutral.py`: kiest per nieuwsfeit de meest neutrale versie (bron, taal, geladen woorden, opinie of niet).
- `fetcher/translate.py`: offline vertaling met de open-source modellen van Argos Translate (geen account of betaling nodig).
- `fetcher/vault.py`: versleutelt de volledige teksten met je wachtwoord (`app/data/texts.bin`).
- `app/`: de app zelf (installeerbaar op Android als web-app).
