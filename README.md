# Feed Me

Persoonlijke nieuwsapp: België, Brussel, tech en de wereld via lokale bronnen, zonder sensatiemedia.
Per nieuwsfeit zie je welke media erover berichten en uit welke politieke hoek ze komen.
Franse en Engelse artikels worden gratis en offline naar het Nederlands vertaald.

## Starten op je pc

Dubbelklik op **Feed Me starten.bat**. Die haalt het nieuws op, vertaalt het en opent de app in je browser.
De eerste keer installeert hij de vertaler en downloadt hij de vertaalmodellen (± 170 MB).

## Hoe het werkt

- `fetcher/sources.py`: de bronnenlijst, politieke labels, geweerde sensatiemedia en klikaas-filters. Hier pas je alles aan.
- `fetcher/fetch_news.py`: haalt de RSS-feeds op, filtert, vertaalt, groepeert per nieuwsfeit en schrijft `app/data/news.json`.
- `fetcher/translate.py`: offline vertaling met de open-source modellen van Argos Translate (geen account of betaling nodig).
- `app/`: de app zelf (installeerbaar op Android als web-app).

## Nog te doen

1. Online zetten via GitHub Pages + GitHub Actions (ververst elke 30 minuten) en installeren op je gsm.
