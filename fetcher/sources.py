"""Bronnenlijst en kwaliteitsregels voor Feed Me.

Pas dit bestand aan om bronnen toe te voegen, te schrappen of hun label te wijzigen.

lean (politieke kleur, enkel voor Belgische/Europese duiding):
    "L"  = links          "CL" = centrum-links     "C" = centrum
    "CR" = centrum-rechts "R"  = rechts            None = geen label (tech, buitenland)
Dit zijn VOORSTELLEN op basis van algemene reputatie, geen objectieve waarheid. De Belgische labels zijn op
10 november 2026 nagekeken tegen Media Bias/Fact Check, Eurotopics en de Reuters Digital News Report (zie
tests/links-rechts.md). Regels: openbare omroepen krijgen hetzelfde label (VRT en RTBF: C); media met hetzelfde
externe profiel ook (De Standaard en La Libre: C).

kind:
    "be"      = Belgische algemene nieuwsbron
    "brussel" = Brusselse lokale bron
    "spanje"  = Spaanse bron (binnenlands nieuws komt in Spanje, buitenlands nieuws in Wereld)
    "tech"    = technologie
    "world"   = buitenlandse (lokale) bron

max_age_h (optioneel): hoe oud artikels mogen zijn, voor bronnen die weinig publiceren (standaard 36 uur)
max_items (optioneel): maximum aantal artikels per update, voor bronnen die heel veel publiceren (standaard 40)
"""

# Talen waarin je Feed Me kan lezen. Standaard enkel Nederlands: zo blijft een update snel.
# Zet er "fr" en/of "en" bij en de app toont in de instellingen een taalkeuze; elke extra taal kost wel vertaaltijd
# (titels, samenvattingen en volledige artikels worden dan ook naar die taal vertaald).
LANGUAGES = ("nl",)

SOURCES = [
    # --- België (Nederlandstalig) ---
    {"id": "vrt", "name": "VRT NWS", "url": "https://www.vrt.be/vrtnws/nl.rss.articles.xml", "lang": "nl", "country": "BE", "kind": "be", "lean": "C"},
    {"id": "standaard", "name": "De Standaard", "url": "https://www.standaard.be/rss", "lang": "nl", "country": "BE", "kind": "be", "lean": "C"},
    {"id": "demorgen", "name": "De Morgen", "url": "https://www.demorgen.be/rss.xml", "lang": "nl", "country": "BE", "kind": "be", "lean": "CL"},
    {"id": "tijd", "name": "De Tijd", "url": "https://www.tijd.be/rss/nieuws.xml", "lang": "nl", "country": "BE", "kind": "be", "lean": "CR"},
    {"id": "knack", "name": "Knack", "url": "https://www.knack.be/feed/", "lang": "nl", "country": "BE", "kind": "be", "lean": "C"},
    {"id": "mo", "name": "MO*", "url": "https://www.mo.be/rss.xml", "lang": "nl", "country": "BE", "kind": "be", "lean": "L"},
    {"id": "pallieterke", "name": "'t Pallieterke", "url": "https://pallieterke.net/feed/", "lang": "nl", "country": "BE", "kind": "be", "lean": "R"},
    # --- België (Franstalig) ---
    {"id": "rtbf", "name": "RTBF", "url": "https://rss.rtbf.be/article/rss/highlight_rtbf_info.xml", "lang": "fr", "country": "BE", "kind": "be", "lean": "C"},
    {"id": "lalibre", "name": "La Libre", "url": "https://www.lalibre.be/arc/outboundfeeds/rss/?outputType=xml", "lang": "fr", "country": "BE", "kind": "be", "lean": "C"},
    {"id": "lecho", "name": "L'Echo", "url": "https://www.lecho.be/rss/actualite.xml", "lang": "fr", "country": "BE", "kind": "be", "lean": "CR"},
    # --- Brussel ---
    {"id": "bruzz", "name": "Bruzz", "url": "https://www.bruzz.be/rss.xml", "lang": "nl", "country": "BE", "kind": "brussel", "lean": "C"},
    # --- Spanje (Spaanstalig; labels volgens het Spaanse politieke landschap) ---
    {"id": "elpais", "name": "El País", "url": "https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada", "lang": "es", "country": "ES", "kind": "spanje", "lean": "CL", "max_items": 25},
    {"id": "eldiario", "name": "elDiario.es", "url": "https://www.eldiario.es/rss/", "lang": "es", "country": "ES", "kind": "spanje", "lean": "L", "max_items": 15},
    {"id": "20minutos", "name": "20minutos", "url": "https://www.20minutos.es/rss/", "lang": "es", "country": "ES", "kind": "spanje", "lean": "C", "max_items": 20},
    {"id": "lavanguardia", "name": "La Vanguardia", "url": "https://www.lavanguardia.com/rss/home.xml", "lang": "es", "country": "ES", "kind": "spanje", "lean": "C", "max_items": 15},
    {"id": "elconfidencial", "name": "El Confidencial", "url": "https://rss.elconfidencial.com/espana/", "lang": "es", "country": "ES", "kind": "spanje", "lean": "CR"},
    {"id": "elmundo", "name": "El Mundo", "url": "https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml", "lang": "es", "country": "ES", "kind": "spanje", "lean": "CR", "max_items": 15},
    {"id": "abc", "name": "ABC", "url": "https://www.abc.es/rss/2.0/portada/", "lang": "es", "country": "ES", "kind": "spanje", "lean": "R", "max_items": 15},
    # --- Europa ---
    {"id": "politico", "name": "Politico Europe", "url": "https://www.politico.eu/feed/", "lang": "en", "country": "EU", "kind": "world", "lean": "C"},
    # --- Tech ---
    {"id": "datanews", "name": "Data News", "url": "https://datanews.knack.be/feed/", "lang": "nl", "country": "BE", "kind": "tech", "lean": None},
    {"id": "tweakers", "name": "Tweakers", "url": "https://tweakers.net/feeds/nieuws.xml", "lang": "nl", "country": "NL", "kind": "tech", "lean": None},
    {"id": "verge", "name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "lang": "en", "country": "US", "kind": "tech", "lean": None},
    {"id": "ars", "name": "Ars Technica", "url": "https://feeds.arstechnica.com/arstechnica/index", "lang": "en", "country": "US", "kind": "tech", "lean": None},
    # --- Wereld: lokale bronnen uit het land zelf ---
    {"id": "nos", "name": "NOS", "url": "https://feeds.nos.nl/nosnieuwsbuitenland", "lang": "nl", "country": "NL", "kind": "world", "lean": None},
    {"id": "kyivind", "name": "Kyiv Independent", "url": "https://kyivindependent.com/news-archive/rss/", "lang": "en", "country": "UA", "kind": "world", "lean": None},
    {"id": "meduza", "name": "Meduza", "url": "https://meduza.io/rss/en/all", "lang": "en", "country": "RU", "kind": "world", "lean": None},
    {"id": "toi", "name": "Times of Israel", "url": "https://www.timesofisrael.com/feed/", "lang": "en", "country": "IL", "kind": "world", "lean": None},
    {"id": "aljazeera", "name": "Al Jazeera", "url": "https://www.aljazeera.com/xml/rss/all.xml", "lang": "en", "country": "QA", "kind": "world", "lean": None},
    {"id": "lemonde", "name": "Le Monde", "url": "https://www.lemonde.fr/international/rss_full.xml", "lang": "fr", "country": "FR", "kind": "world", "lean": None},
    {"id": "spiegel", "name": "Der Spiegel", "url": "https://www.spiegel.de/international/index.rss", "lang": "en", "country": "DE", "kind": "world", "lean": None, "max_age_h": 120},
    {"id": "bbc", "name": "BBC", "url": "https://feeds.bbci.co.uk/news/world/rss.xml", "lang": "en", "country": "GB", "kind": "world", "lean": None},
    {"id": "hindu", "name": "The Hindu", "url": "https://www.thehindu.com/news/international/feeder/default.rss", "lang": "en", "country": "IN", "kind": "world", "lean": None},
    {"id": "scmp", "name": "South China Morning Post", "url": "https://www.scmp.com/rss/91/feed", "lang": "en", "country": "HK", "kind": "world", "lean": None},
    {"id": "japantimes", "name": "Japan Times", "url": "https://www.japantimes.co.jp/feed/", "lang": "en", "country": "JP", "kind": "world", "lean": None},
    {"id": "africanews", "name": "Africanews", "url": "https://www.africanews.com/feed/rss", "lang": "en", "country": "AFRICA", "kind": "world", "lean": None},
    {"id": "mercopress", "name": "MercoPress", "url": "https://en.mercopress.com/rss/", "lang": "en", "country": "LATAM", "kind": "world", "lean": None},
    {"id": "dw", "name": "DW", "url": "https://rss.dw.com/rdf/rss-en-all", "lang": "en", "country": "DE", "kind": "world", "lean": None},
    {"id": "ansa", "name": "ANSA", "url": "https://www.ansa.it/english/news/english_nr_rss.xml", "lang": "en", "country": "IT", "kind": "world", "lean": None, "max_items": 20},
    {"id": "notesfrompoland", "name": "Notes from Poland", "url": "https://notesfrompoland.com/feed/", "lang": "en", "country": "PL", "kind": "world", "lean": None, "max_age_h": 96},
    {"id": "err", "name": "ERR News", "url": "https://news.err.ee/rss", "lang": "en", "country": "EE", "kind": "world", "lean": None, "max_items": 20},
    {"id": "balkaninsight", "name": "Balkan Insight", "url": "https://balkaninsight.com/feed/", "lang": "en", "country": "BALKAN", "kind": "world", "lean": None, "max_age_h": 72},
    {"id": "npr", "name": "NPR", "url": "https://feeds.npr.org/1001/rss.xml", "lang": "en", "country": "US", "kind": "world", "lean": None},
    {"id": "cbc", "name": "CBC", "url": "https://www.cbc.ca/webfeed/rss/rss-topstories", "lang": "en", "country": "CA", "kind": "world", "lean": None},
    {"id": "abcau", "name": "ABC Australia", "url": "https://www.abc.net.au/news/feed/51120/rss.xml", "lang": "en", "country": "AU", "kind": "world", "lean": None},
    {"id": "yonhap", "name": "Yonhap", "url": "https://en.yna.co.kr/RSS/news.xml", "lang": "en", "country": "KR", "kind": "world", "lean": None, "max_items": 20},
    {"id": "straitstimes", "name": "The Straits Times", "url": "https://www.straitstimes.com/news/world/rss.xml", "lang": "en", "country": "SG", "kind": "world", "lean": None, "max_items": 20},
    {"id": "rappler", "name": "Rappler", "url": "https://www.rappler.com/feed/", "lang": "en", "country": "PH", "kind": "world", "lean": None},
    {"id": "dailymaverick", "name": "Daily Maverick", "url": "https://www.dailymaverick.co.za/dmrss/", "lang": "en", "country": "ZA", "kind": "world", "lean": None},
    {"id": "premiumtimes", "name": "Premium Times", "url": "https://www.premiumtimesng.com/feed", "lang": "en", "country": "NG", "kind": "world", "lean": None},
]

# --- Kwaliteitsregel 1: geen sensatie- en boulevardmedia ---
# Bronnen van deze domeinen worden nooit getoond, ook niet als ze via een andere feed binnenkomen.
BLOCKED_DOMAINS = [
    # België
    "hln.be", "nieuwsblad.be", "gva.be", "hbvl.be", "dhnet.be", "sudinfo.be", "7sur7.be", "nieuws.vtm.be",
    # Nederland
    "telegraaf.nl", "geenstijl.nl", "dumpert.nl",
    # VK / VS
    "dailymail.co.uk", "thesun.co.uk", "mirror.co.uk", "express.co.uk", "dailystar.co.uk", "nypost.com", "tmz.com",
    # Duitsland / Frankrijk
    "bild.de", "closermag.fr", "voici.fr",
]

# --- Kwaliteitsregel 2: klikaas en reclame eruit ---
# Titels die hierop matchen worden weggefilterd (hoofdletterongevoelig).
CLICKBAIT_PATTERNS = [
    r"^\s*(bekijk|kijk|quiz|poll|test jezelf|horoscoop|horoscope)\b",
    r"\b(dit moet je|je gelooft nooit|niet te geloven|je zal versteld|wat er daarna gebeurde)\b",
    r"\b(you won't believe|what happened next|incroyable mais vrai)\b",
    r"\b(partnercontent|advertorial|gesponsord|sponsored|in samenwerking met|publireportage)\b",
    r"\b(winactie|win een|concours|gagnez)\b",
    r"\b(deals?|on sale|% off|korting|aanbieding|bons plans|promo)\b",
    r"!!|[\U0001F600-\U0001F64F\U0001F525\U0001F631]",
]

# --- Spaanse bronnen: de rubriek staat in het webadres (elpais.com/internacional/...) ---
# Zo komt enkel nieuws óver Spanje in de rubriek Spanje. Rubrieken die hier niet staan tellen als Spaans nieuws.
SPAIN_PATH_SECTIONS = {
    "internacional": "wereld", "mundo": "wereld", "america": "wereld", "us": "wereld", "latinoamerica": "wereld",
    "tecnologia": "tech", "ciencia": "wetenschap",
}
# staat er een ander land in de (Spaanse) titel en niets over Spanje, dan is het buitenlands nieuws
SPAIN_FOREIGN = (r"ee\.? ?uu\.?|estados unidos|trump|rusia|ucrania|putin|israel|gaza|irán|china|méxico|sheinbaum"
                 r"|francia|alemania|italia|reino unido|londres|parís|nueva york|venezuela|argentina|brasil|colombia")
# winkeltips, roddels en lifestyle: geen nieuws, dus overslaan
SPAIN_SKIP_PATHS = {
    "comprar", "compras", "ofertas-descuentos", "escaparate", "gente", "television", "cinemania", "mujer",
    "gastronomia", "viajes", "fotos", "play", "spin", "estilo", "moda", "horoscopo", "recetas", "bienestar", "loc",
}

# --- Interesses: welke rubrieken krijgen voorrang in "Voor jou" ---
INTEREST_BOOST = {
    "brussel": 1.6, "belgie": 1.35, "tech": 1.35, "spanje": 1.3, "europa": 1.15,
    "economie": 1.05, "wetenschap": 1.05, "mobiliteit": 1.05, "conflicten": 1.0, "wereld": 1.0,
}

# --- Rubrieken op onderwerp ---
# Een artikel komt in een rubriek als een van deze woorden in de titel staat,
# of als er minstens twee verschillende in de samenvatting staan.
TOPICS = {
    "spanje": r"spanje|spaans\w*|madrid\w*|barcelona|catalon\w*|catala\w*|andalus\w*|valencia\w*|sevilla|bilbao|baskisch\w*"
              r"|mallorca|canarische|ibiza|málaga|malaga|sánchez|feijóo|psoe|espagne|spain|spanish|españa|español\w*",
    "europa": r"europese (commissie|unie|raad|centrale bank)|europees parlement|eu-\w+|eu|von der leyen|kallas|eurozone"
              r"|schengen|europarlement\w*|commission européenne|union européenne|european commission|european union",
    "conflicten": r"oorlog\w*|oekraïn\w*|ukrain\w*|kyiv|kiev|kremlin|gaza|hamas|hezbollah|westelijke jordaanoever|west bank"
                  r"|soedan|sudan|congo|m23|houthi\w*|jemen|drone-?aanval\w*|raketaanval\w*|luchtaanval\w*|staakt-het-vuren"
                  r"|wapenstilstand|ceasefire|troepen|bombardement\w*|frontlinie|offensief|guerre|war",
    "economie": r"econom\w*|beurs\w*|aandel\w*|bedrijf\w*|omzet|winst|faillissement\w*|overname\w*|fusie|banen|jobs?"
                r"|werkloos\w*|herstructurering|lonen|loon\w*|inflatie|rente\w*|ecb|begroting\w*|btw|belasting\w*"
                r"|pensioen\w*|koopkracht|investering\w*|export|handelsoorlog|invoerheffing\w*|tarieven|bbp|recessie"
                r"|vakbond\w*|staking\w*",
    "wetenschap": r"wetenschap\w*|onderzoekers|studie|universiteit\w*|nasa|esa|ruimtevaart\w*|ruimte|planeet\w*|astronom\w*"
                  r"|telescoop|fossiel\w*|dna|genetisch\w*|gezondheid\w*|kanker|vaccin\w*|virus\w*|ebola"
                  r"|epidemie|pandemie|artsen|medicijn\w*|geneesmiddel\w*|hersen\w*|ziekte\w*|griep",
    "mobiliteit": r"verkeer\w*|file|files|trein\w*|nmbs|sncb|de lijn|mivb|stib|tram\w*|metro|fiets\w*|snelweg\w*|tunnel\w*"
                  r"|luchthaven\w*|zaventem|spoor\w*|mobiliteit\w*|woningmarkt|woningprijzen|huurwoning\w*|sociale woning\w*"
                  r"|huurprijs\w*|huurder\w*|vastgoed\w*|renovatie\w*|wonen"
                  r"|appartement\w*|hypothe\w*|rijbewijs|parkeer\w*|lez",
}
