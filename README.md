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

## Hoe het werkt

- `fetcher/sources.py`: de bronnenlijst, politieke labels, geweerde sensatiemedia en klikaas-filters. Hier pas je alles aan.
- `fetcher/fetch_news.py`: haalt de RSS-feeds op, filtert, vertaalt, groepeert per nieuwsfeit en schrijft `app/data/news.json`.
- `fetcher/articles.py`: haalt de volledige tekst van elk artikel op. Betaal- en loginmuren worden gerespecteerd.
- `fetcher/neutral.py`: kiest per nieuwsfeit de meest neutrale versie (bron, volledige tekst, geladen woorden, opinie of niet).
- `fetcher/translate.py`: offline vertaling met de open-source modellen van Argos Translate (geen account of betaling nodig).
- `fetcher/search.py`: zoekt een gratis versie van nieuws dat enkel achter een betaalmuur staat.
- `fetcher/summary.py`: maakt de korte samenvatting (de belangrijkste zinnen uit het artikel zelf).
- `fetcher/vault.py`: versleutelt de volledige teksten met je wachtwoord (`app/data/texts.bin`).
- `app/`: de app zelf (installeerbaar op Android als web-app).
