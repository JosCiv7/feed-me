// Feed Me: persoonlijke nieuwsapp. Rubrieken (en de taal, als er meer dan één is: zie LANGUAGES in fetcher/sources.py)
// kies je in de instellingen; die worden enkel op dit toestel bewaard.
const PAGE_SIZE = 20;
const PBKDF2_ITERATIONS = 150000; // moet gelijk zijn aan fetcher/vault.py
const LANGS = ["nl", "fr", "en"];
const LOCALE = { nl: "nl-BE", fr: "fr-BE", en: "en-GB" };
const LEANS = ["L", "CL", "C", "CR", "R"];
const STAR_BOOST = 1.3; // extra voorrang voor een rubriek met een ster

// rubrieken in de volgorde van de voorpagina, met hun naam per taal (block = langere titel boven het blok)
const THEMES = [
  { id: "belgie", name: { nl: "België", fr: "Belgique", en: "Belgium" } },
  { id: "brussel", name: { nl: "Brussel", fr: "Bruxelles", en: "Brussels" } },
  { id: "spanje", name: { nl: "Spanje", fr: "Espagne", en: "Spain" } },
  { id: "europa", name: { nl: "Europa", fr: "Europe", en: "Europe" } },
  { id: "conflicten", name: { nl: "Conflicten", fr: "Conflits", en: "Conflicts" } },
  { id: "economie", name: { nl: "Economie", fr: "Économie", en: "Economy" }, block: { nl: "Economie & werk", fr: "Économie & emploi", en: "Economy & work" } },
  { id: "tech", name: { nl: "Tech", fr: "Tech", en: "Tech" } },
  { id: "wetenschap", name: { nl: "Wetenschap", fr: "Sciences", en: "Science" }, block: { nl: "Wetenschap & gezondheid", fr: "Sciences & santé", en: "Science & health" } },
  { id: "mobiliteit", name: { nl: "Mobiliteit", fr: "Mobilité", en: "Mobility" }, block: { nl: "Mobiliteit & wonen", fr: "Mobilité & logement", en: "Mobility & housing" } },
  { id: "wereld", name: { nl: "Wereld", fr: "Monde", en: "World" } },
].map((x) => ({ ...x, color: `var(--sec-${x.id})` }));
const THEME = Object.fromEntries(THEMES.map((x) => [x.id, x]));
// voorrang voor het label boven een verhaal: eerst plaats, dan onderwerp
const KICKER_ORDER = ["brussel", "belgie", "spanje", "europa", "conflicten", "economie", "tech", "wetenschap", "mobiliteit", "wereld"];

// --- teksten in drie talen ---
const I18N = {
  nl: {
    forYou: "Voor jou", sources: "Bronnen", settings: "Instellingen", install: "Installeer app", refresh: "Vernieuwen",
    newNews: "Nieuw nieuws beschikbaar", tapRefresh: "Tik om te vernieuwen", loading: "Nieuws laden…",
    password: "Wachtwoord", open: "Openen", wrongPw: "Dat wachtwoord klopt niet.", loadFail: "Nieuws kon niet geladen worden. Ben je online?",
    justNow: "zonet", ago: (x) => `${x} geleden`, h: "u", d: "d", updated: (x) => `Bijgewerkt ${x}`,
    broad: "Breed gedragen", broadSub: "Verhalen die door veel media gebracht worden", latest: "Net binnen", more: "Meer nieuws", all: "Alles ›",
    emptyTheme: "Nog geen nieuws in deze rubriek.", emptyAll: "Geen nieuws dat bij je instellingen past. Zet meer rubrieken aan in de instellingen.",
    endTitle: "Je bent helemaal mee.", endText: (h) => `Dit was al het nieuws van de laatste ${h} uur.`,
    nSources: (n) => `${n} bronnen`, blind: "Blinde vlek", blindLeft: "vooral links", blindRight: "vooral rechts",
    autoTr: "Automatisch vertaald", translatedFrom: (l) => `Vertaald uit het ${l}`,
    leans: { L: "Links", CL: "Centrum-links", C: "Centrum", CR: "Centrum-rechts", R: "Rechts" },
    mostNeutralOf: (n) => `Meest neutrale versie van ${n} bronnen`,
    why: { found: "gratis versie, gevonden via zoeken omdat de andere bronnen achter een muur zitten", text: "volledige tekst leesbaar in de app",
      loaded0: "geen geladen woorden gevonden", loaded: (n) => `${n} geladen woord${n > 1 ? "en" : ""}`, others: (n) => `vergeleken met ${n} andere versie${n > 1 ? "s" : ""}`,
      lean: { C: "centrumbron", CL: "centrum-links", CR: "centrum-rechts", L: "linkse bron", R: "rechtse bron" } },
    youRead: (s) => `Je leest de versie van ${s}`, neutralFrom: (s) => `De meest neutrale versie komt van ${s}.`, readThat: "Lees die versie",
    compareTitle: (n) => `Zo brengen ${n} media dit verhaal`, compareText: "Vergelijk de titels en woordkeuze. Tik op een versie om ze te lezen.",
    oneSource: "Eén bron", onlyOne: (s) => `Enkel ${s} brengt dit verhaal (in de bronnen van Feed Me).`, loadedIn: "Geladen woorden in dit artikel:",
    loadedWords: "Geladen woorden:", noLoaded: "Geen geladen woorden gevonden", notMeasured: "Toon niet gemeten (geen vrije tekst)",
    bMostNeutral: "Meest neutraal", bFound: "Gevonden via zoeken", bOpinion: "Opinie/analyse", bLive: "Liveblog", bText: "Tekst in app", bLink: "Enkel link",
    origAt: (s) => `Origineel artikel bij ${s} ↗`, readAt: (s) => `Lees bij ${s} ↗`, readAtShort: (s) => `Lees bij ${s}`, back: "Terug",
    noText: { betaalmuur: "zit achter een betaalmuur", inlogmuur: "vraagt om in te loggen of cookies te aanvaarden", geweigerd: "laat geen automatische lezers toe", "te kort": "geeft geen volledige tekst vrij" },
    noTextWhy: (s, r) => `${s} ${r}, dus de volledige tekst staat niet in Feed Me.`, noTextAny: "De volledige tekst kon (nog) niet gelezen worden.",
    summary: "Kort samengevat", summaryNote: "De belangrijkste zinnen uit het artikel zelf, automatisch gekozen.",
    showOrig: "Toon origineel", showTr: "Toon vertaling", untranslated: "De vertaling van dit artikel volgt bij een volgende update; hieronder de originele tekst.",
    articleLoading: "Artikel laden…", articlesFail: "De artikels konden niet geladen worden.",
    latestNews: (x) => `Je hebt het nieuwste nieuws (bijgewerkt ${x})`, refreshFail: "Vernieuwen lukt niet. Ben je online?",
    installed: "Feed Me staat nu als app tussen je apps.",
    // instellingen
    // wachtwoord voor de volledige artikels en zelf een update starten
    pwTitle: "Volledig artikel lezen", pwWhy: "De volledige artikels zijn beveiligd met een wachtwoord. Je hoeft het maar één keer in te geven.",
    ghTitle: "Zelf nieuw nieuws laten ophalen",
    ghIntro: (m) => `GitHub slaat zijn vaste updates soms urenlang over. Met een sleutel kan deze knop zelf een update starten (± ${m} minuten). Je doet dit maar één keer:`,
    ghSteps: ['Open <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">deze GitHub-pagina</a> en meld je aan.', "Naam: <i>Feed Me</i>. Vervaldatum: zo lang mogelijk.",
      "Bij <i>Repository access</i>: <i>Only select repositories</i> → <i>feed-me</i>.", "Bij <i>Permissions</i>: <i>Actions</i> → <i>Read and write</i>. Verder niets.",
      "Tik op <i>Generate token</i>, kopieer de sleutel en plak hem hieronder."],
    ghWhy: "De sleutel blijft enkel op dit toestel en kan alleen updates van Feed Me starten.", ghKey: "GitHub-sleutel", ghSave: "Opslaan en nieuws ophalen", ghLater: "Later",
    ghBadKey: "Die sleutel werkt niet (meer). Maak een nieuwe aan.", ghNoRights: "Die sleutel mag geen updates starten. Kijk na of je bij Actions 'Read and write' koos.",
    updStarted: (m) => `Nieuws wordt opgehaald. Binnen ±${m} minuten verschijnt bovenaan een melding.`,
    updWaiting: "Het nieuws wordt nog opgehaald. Je krijgt bovenaan een melding als het klaar is.",
    sTitle: "Instellingen", sIntro: "Kies wat je wil zien. Je keuzes worden enkel op dit toestel bewaard.",
    sLang: "Taal", sLangHelp: "Taal van de app, de titels en de artikels (automatisch vertaald waar nodig).",
    sThemes: "Rubrieken", sThemesHelp: "Kies welke rubrieken je wil zien. Met de ster krijgt een rubriek extra voorrang in \"Voor jou\".",
    sStar: "Extra voorrang", sReset: "Alles terugzetten naar standaard", sLock: "Wachtwoord vergeten op dit toestel", sPwSaved: "Je wachtwoord is bewaard op dit toestel.",
    // bronnenpagina
    aboutTitle: "Hoe werkt Feed Me?",
    about: (n) => `Feed Me verzamelt het nieuws van ${n} bronnen en legt artikels over hetzelfde nieuwsfeit samen. Per verhaal zie je welke media erover berichten en uit welke hoek ze komen.`,
    aboutNeutral: "Meest neutrale versie. Als meerdere media hetzelfde verhaal brengen, toont Feed Me de meest neutrale versie: liefst een centrumbron, met volledige tekst, met zo weinig mogelijk geladen woorden (zoals \"schandalig\", \"chaos\" of \"slams\") en geen opiniestuk. Onder elk artikel zie je hoe de andere media het brengen.",
    aboutRead: "Lezen in de app. Waar de site het toelaat, staat de volledige tekst in de app. Betaal- en loginmuren worden gerespecteerd. Staat een verhaal enkel achter zo'n muur, dan zoekt Feed Me een ander medium dat hetzelfde nieuws gratis brengt. Lukt dat niet, dan krijg je een link naar de site. De teksten zijn versleuteld met je wachtwoord, zodat enkel jij ze kan lezen.",
    aboutTranslate: "Vertaling. Franse, Spaanse en Engelse artikels worden automatisch en gratis naar het Nederlands vertaald (label FR→NL). De vertaling is niet perfect; het origineel kan je altijd bekijken.",
    aboutBlind: "Een blinde vlek betekent dat een verhaal bijna enkel door linkse of enkel door rechtse media wordt gebracht. De politieke labels zijn een voorstel; hoe ze nagekeken zijn, staat in tests/links-rechts.md.",
    groups: { be: "België", brussel: "Brussel", spanje: "Spanje", tech: "Tech", world: "Wereld & Europa", web: "Gratis versies gevonden via zoeken" },
    unreachable: "niet bereikbaar", textInApp: "tekst in de app", linkOnly: "enkel link",
    blockedTitle: "Geweerd: sensatie & boulevard", blockedText: "Deze media worden nooit getoond. Ook titels met klikaas, quizzen, reclame of \"deals\" worden eruit gefilterd.",
    places: { AFRICA: "Afrika", LATAM: "Latijns-Amerika", BALKAN: "Balkan", EU: "Europa", HK: "Hongkong" },
  },
  fr: {
    forYou: "Pour vous", sources: "Sources", settings: "Paramètres", install: "Installer l'app", refresh: "Actualiser",
    newNews: "Nouvelles actualités disponibles", tapRefresh: "Touchez pour actualiser", loading: "Chargement…",
    password: "Mot de passe", open: "Ouvrir", wrongPw: "Ce mot de passe est incorrect.", loadFail: "Impossible de charger les actualités. Êtes-vous en ligne ?",
    justNow: "à l'instant", ago: (x) => `il y a ${x}`, h: "h", d: "j", updated: (x) => `Mis à jour ${x}`,
    broad: "Largement relayé", broadSub: "Des sujets couverts par de nombreux médias", latest: "Dernières nouvelles", more: "Plus d'actualités", all: "Tout ›",
    emptyTheme: "Pas encore d'actualités dans cette rubrique.", emptyAll: "Aucune actualité ne correspond à vos paramètres. Activez plus de rubriques dans les paramètres.",
    endTitle: "Vous êtes à jour.", endText: (h) => `C'était toute l'actualité des ${h} dernières heures.`,
    nSources: (n) => `${n} sources`, blind: "Angle mort", blindLeft: "surtout à gauche", blindRight: "surtout à droite",
    autoTr: "Traduit automatiquement", translatedFrom: (l) => `Traduit de l'original en ${l}`,
    leans: { L: "Gauche", CL: "Centre gauche", C: "Centre", CR: "Centre droit", R: "Droite" },
    mostNeutralOf: (n) => `Version la plus neutre parmi ${n} sources`,
    why: { found: "version gratuite trouvée par recherche, les autres sources étant derrière un mur", text: "texte intégral lisible dans l'app",
      loaded0: "aucun mot chargé trouvé", loaded: (n) => `${n} mot${n > 1 ? "s" : ""} chargé${n > 1 ? "s" : ""}`, others: (n) => `comparée à ${n} autre${n > 1 ? "s" : ""} version${n > 1 ? "s" : ""}`,
      lean: { C: "source centriste", CL: "centre gauche", CR: "centre droit", L: "source de gauche", R: "source de droite" } },
    youRead: (s) => `Vous lisez la version de ${s}`, neutralFrom: (s) => `La version la plus neutre vient de ${s}.`, readThat: "Lire cette version",
    compareTitle: (n) => `Comment ${n} médias traitent ce sujet`, compareText: "Comparez les titres et le choix des mots. Touchez une version pour la lire.",
    oneSource: "Une seule source", onlyOne: (s) => `Seul ${s} traite ce sujet (parmi les sources de Feed Me).`, loadedIn: "Mots chargés dans cet article :",
    loadedWords: "Mots chargés :", noLoaded: "Aucun mot chargé trouvé", notMeasured: "Ton non mesuré (pas de texte libre)",
    bMostNeutral: "La plus neutre", bFound: "Trouvée par recherche", bOpinion: "Opinion/analyse", bLive: "Direct", bText: "Texte dans l'app", bLink: "Lien seulement",
    origAt: (s) => `Article original sur ${s} ↗`, readAt: (s) => `Lire sur ${s} ↗`, readAtShort: (s) => `Lire sur ${s}`, back: "Retour",
    noText: { betaalmuur: "est derrière un paywall", inlogmuur: "demande de se connecter ou d'accepter des cookies", geweigerd: "n'autorise pas les lecteurs automatiques", "te kort": "ne publie pas le texte intégral" },
    noTextWhy: (s, r) => `${s} ${r} : le texte intégral n'est donc pas dans Feed Me.`, noTextAny: "Le texte intégral n'a pas (encore) pu être lu.",
    summary: "En bref", summaryNote: "Les phrases principales de l'article lui-même, choisies automatiquement.",
    showOrig: "Voir l'original", showTr: "Voir la traduction", untranslated: "La traduction de cet article suivra lors d'une prochaine mise à jour ; voici le texte original.",
    articleLoading: "Chargement de l'article…", articlesFail: "Impossible de charger les articles.",
    latestNews: (x) => `Vous avez les dernières actualités (mises à jour ${x})`, refreshFail: "Impossible d'actualiser. Êtes-vous en ligne ?",
    installed: "Feed Me est maintenant installé comme application.",
    pwTitle: "Lire l'article complet", pwWhy: "Les articles complets sont protégés par un mot de passe. Vous ne devez le saisir qu'une seule fois.",
    ghTitle: "Lancer soi-même une mise à jour",
    ghIntro: (m) => `GitHub saute parfois ses mises à jour planifiées pendant des heures. Avec une clé, ce bouton peut lancer lui-même une mise à jour (± ${m} minutes). Vous ne faites ceci qu'une seule fois :`,
    ghSteps: ['Ouvrez <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">cette page GitHub</a> et connectez-vous.', "Nom : <i>Feed Me</i>. Expiration : la plus longue possible.",
      "Sous <i>Repository access</i> : <i>Only select repositories</i> → <i>feed-me</i>.", "Sous <i>Permissions</i> : <i>Actions</i> → <i>Read and write</i>. Rien d'autre.",
      "Cliquez sur <i>Generate token</i>, copiez la clé et collez-la ci-dessous."],
    ghWhy: "La clé reste uniquement sur cet appareil et ne peut que lancer des mises à jour de Feed Me.", ghKey: "Clé GitHub", ghSave: "Enregistrer et actualiser", ghLater: "Plus tard",
    ghBadKey: "Cette clé ne fonctionne pas (ou plus). Créez-en une nouvelle.", ghNoRights: "Cette clé ne peut pas lancer de mise à jour. Vérifiez que vous avez choisi « Read and write » sous Actions.",
    updStarted: (m) => `Mise à jour en cours. Un message apparaîtra en haut dans ±${m} minutes.`,
    updWaiting: "La mise à jour est encore en cours. Un message apparaîtra en haut quand elle sera terminée.",
    sTitle: "Paramètres", sIntro: "Réglez Feed Me comme vous le souhaitez. Vos choix ne sont enregistrés que sur cet appareil.",
    sLang: "Langue", sLangHelp: "Langue de l'app, des titres et des articles (traduits automatiquement si nécessaire).",
    sThemes: "Rubriques", sThemesHelp: "Choisissez les rubriques à afficher. L'étoile donne une priorité supplémentaire dans « Pour vous ».",
    sStar: "Priorité supplémentaire", sReset: "Tout remettre par défaut", sLock: "Oublier le mot de passe sur cet appareil", sPwSaved: "Votre mot de passe est enregistré sur cet appareil.",
    aboutTitle: "Comment fonctionne Feed Me ?",
    about: (n) => `Feed Me rassemble l'actualité de ${n} sources et regroupe les articles sur un même fait. Pour chaque sujet, vous voyez quels médias en parlent et de quel bord ils sont.`,
    aboutNeutral: "Version la plus neutre. Quand plusieurs médias couvrent un sujet, Feed Me montre la version la plus neutre : de préférence une source centriste, avec texte intégral, le moins possible de mots chargés et pas d'opinion. Sous chaque article, vous voyez comment les autres médias le présentent.",
    aboutRead: "Lire dans l'app. Quand le site le permet, le texte intégral est dans l'app. Les paywalls et pages de connexion sont respectés. Si un sujet n'existe que derrière un tel mur, Feed Me cherche un autre média qui le publie gratuitement ; sinon vous recevez un lien vers le site. Les textes sont chiffrés avec votre mot de passe.",
    aboutTranslate: "Traduction. Les articles sont traduits automatiquement et gratuitement dans la langue choisie dans les paramètres. La traduction n'est pas parfaite ; l'original reste toujours consultable.",
    aboutBlind: "Un angle mort signifie qu'un sujet est presque uniquement couvert par des médias de gauche ou de droite. Les étiquettes politiques sont une proposition ; leur vérification est décrite dans tests/links-rechts.md.",
    groups: { be: "Belgique", brussel: "Bruxelles", spanje: "Espagne", tech: "Tech", world: "Monde & Europe", web: "Versions gratuites trouvées par recherche" },
    unreachable: "injoignable", textInApp: "texte dans l'app", linkOnly: "lien seulement",
    blockedTitle: "Exclus : presse à sensation", blockedText: "Ces médias ne sont jamais affichés. Les titres racoleurs, quiz, publicités et « bons plans » sont aussi filtrés.",
    places: { AFRICA: "Afrique", LATAM: "Amérique latine", BALKAN: "Balkans", EU: "Europe", HK: "Hong Kong" },
  },
  en: {
    forYou: "For you", sources: "Sources", settings: "Settings", install: "Install app", refresh: "Refresh",
    newNews: "New stories available", tapRefresh: "Tap to refresh", loading: "Loading news…",
    password: "Password", open: "Open", wrongPw: "That password is incorrect.", loadFail: "The news could not be loaded. Are you online?",
    justNow: "just now", ago: (x) => `${x} ago`, h: "h", d: "d", updated: (x) => `Updated ${x}`,
    broad: "Widely covered", broadSub: "Stories covered by many outlets", latest: "Just in", more: "More news", all: "All ›",
    emptyTheme: "No news in this section yet.", emptyAll: "No news matches your settings. Turn on more sections in the settings.",
    endTitle: "You're all caught up.", endText: (h) => `That was all the news from the last ${h} hours.`,
    nSources: (n) => `${n} sources`, blind: "Blind spot", blindLeft: "mostly left", blindRight: "mostly right",
    autoTr: "Automatically translated", translatedFrom: (l) => `Translated from ${l}`,
    leans: { L: "Left", CL: "Centre-left", C: "Centre", CR: "Centre-right", R: "Right" },
    mostNeutralOf: (n) => `Most neutral version of ${n} sources`,
    why: { found: "free version found by search because the other sources are behind a wall", text: "full text readable in the app",
      loaded0: "no loaded words found", loaded: (n) => `${n} loaded word${n > 1 ? "s" : ""}`, others: (n) => `compared with ${n} other version${n > 1 ? "s" : ""}`,
      lean: { C: "centrist source", CL: "centre-left", CR: "centre-right", L: "left-wing source", R: "right-wing source" } },
    youRead: (s) => `You are reading the version from ${s}`, neutralFrom: (s) => `The most neutral version is from ${s}.`, readThat: "Read that version",
    compareTitle: (n) => `How ${n} outlets cover this story`, compareText: "Compare the headlines and wording. Tap a version to read it.",
    oneSource: "One source", onlyOne: (s) => `Only ${s} covers this story (among Feed Me's sources).`, loadedIn: "Loaded words in this article:",
    loadedWords: "Loaded words:", noLoaded: "No loaded words found", notMeasured: "Tone not measured (no free text)",
    bMostNeutral: "Most neutral", bFound: "Found by search", bOpinion: "Opinion/analysis", bLive: "Live blog", bText: "Text in app", bLink: "Link only",
    origAt: (s) => `Original article at ${s} ↗`, readAt: (s) => `Read at ${s} ↗`, readAtShort: (s) => `Read at ${s}`, back: "Back",
    noText: { betaalmuur: "is behind a paywall", inlogmuur: "asks you to log in or accept cookies", geweigerd: "does not allow automated readers", "te kort": "does not publish the full text" },
    noTextWhy: (s, r) => `${s} ${r}, so the full text is not in Feed Me.`, noTextAny: "The full text could not be read (yet).",
    summary: "In short", summaryNote: "The key sentences from the article itself, picked automatically.",
    showOrig: "Show original", showTr: "Show translation", untranslated: "The translation of this article follows in a later update; below is the original text.",
    articleLoading: "Loading article…", articlesFail: "The articles could not be loaded.",
    latestNews: (x) => `You have the latest news (updated ${x})`, refreshFail: "Refreshing failed. Are you online?",
    installed: "Feed Me is now installed as an app.",
    pwTitle: "Read the full article", pwWhy: "The full articles are protected with a password. You only need to enter it once.",
    ghTitle: "Start a news update yourself",
    ghIntro: (m) => `GitHub sometimes skips its scheduled updates for hours. With a key, this button can start an update itself (± ${m} minutes). You only do this once:`,
    ghSteps: ['Open <a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">this GitHub page</a> and sign in.', "Name: <i>Feed Me</i>. Expiration: as long as possible.",
      "Under <i>Repository access</i>: <i>Only select repositories</i> → <i>feed-me</i>.", "Under <i>Permissions</i>: <i>Actions</i> → <i>Read and write</i>. Nothing else.",
      "Click <i>Generate token</i>, copy the key and paste it below."],
    ghWhy: "The key stays on this device only and can only start Feed Me updates.", ghKey: "GitHub key", ghSave: "Save and fetch news", ghLater: "Later",
    ghBadKey: "That key does not work (any more). Create a new one.", ghNoRights: "That key may not start updates. Check that you chose 'Read and write' under Actions.",
    updStarted: (m) => `Fetching news. A notice will appear at the top within ±${m} minutes.`,
    updWaiting: "The news is still being fetched. A notice will appear at the top when it is ready.",
    sTitle: "Settings", sIntro: "Set up Feed Me the way you want. Your choices are only stored on this device.",
    sLang: "Language", sLangHelp: "Language of the app, the headlines and the articles (translated automatically where needed).",
    sThemes: "Sections", sThemesHelp: "Choose which sections you want to see. The star gives a section extra priority in \"For you\".",
    sStar: "Extra priority", sReset: "Reset everything to default", sLock: "Forget the password on this device", sPwSaved: "Your password is saved on this device.",
    aboutTitle: "How does Feed Me work?",
    about: (n) => `Feed Me collects news from ${n} sources and groups articles about the same event. For each story you see which outlets cover it and where they stand.`,
    aboutNeutral: "Most neutral version. When several outlets cover a story, Feed Me shows the most neutral version: preferably a centrist source, with full text, as few loaded words as possible and no opinion piece. Below each article you see how the other outlets present it.",
    aboutRead: "Reading in the app. Where the site allows it, the full text is in the app. Paywalls and login walls are respected. If a story only exists behind such a wall, Feed Me looks for another outlet that publishes it for free; otherwise you get a link to the site. The texts are encrypted with your password.",
    aboutTranslate: "Translation. Articles are translated automatically and for free into the language you choose in the settings. The translation is not perfect; you can always view the original.",
    aboutBlind: "A blind spot means a story is covered almost only by left-wing or only by right-wing outlets. The political labels are a proposal; how they were checked is described in tests/links-rechts.md.",
    groups: { be: "Belgium", brussel: "Brussels", spanje: "Spain", tech: "Tech", world: "World & Europe", web: "Free versions found by search" },
    unreachable: "unreachable", textInApp: "text in app", linkOnly: "link only",
    blockedTitle: "Excluded: tabloids", blockedText: "These outlets are never shown. Headlines with clickbait, quizzes, ads or \"deals\" are filtered out too.",
    places: { AFRICA: "Africa", LATAM: "Latin America", BALKAN: "Balkans", EU: "Europe", HK: "Hong Kong" },
  },
};

// --- opslag (mag falen, bv. in privémodus) ---
const STORE = "";
function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(STORE + key)) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(STORE + key, JSON.stringify(value)); } catch {}
}

// --- persoonlijke instellingen (enkel op dit toestel) ---
function defaultPrefs() {
  return { lang: "nl", off: [], star: [] };
}
let prefs = { ...defaultPrefs(), ...load("prefs", {}) };
const L = () => prefs.lang;
const t = () => I18N[prefs.lang] || I18N.nl;
function savePrefs() { save("prefs", prefs); }

const state = {
  data: null, stories: [], tab: "voorjou", list: [], shown: 0, sources: {}, read: new Set(),
  password: null, showOriginal: false, fromFeed: false,
};
const feed = document.getElementById("feed");
const reader = document.getElementById("reader");

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const themeColor = (id) => THEME[id]?.color || "var(--accent)";
const themeName = (id) => { const n = THEME[id]?.name; return typeof n === "object" ? (n[L()] || n.nl) : (n || id); };
const themeBlock = (id) => { const b = THEME[id]?.block; return typeof b === "object" ? (b[L()] || b.nl) : (b || themeName(id)); };
const regionName = (code) => { if (t().places[code]) return t().places[code]; try { return new Intl.DisplayNames([LOCALE[L()]], { type: "region" }).of(code) || code; } catch { return code; } };
const langName = (code) => { try { return new Intl.DisplayNames([LOCALE[L()]], { type: "language" }).of(code) || code; } catch { return code; } };

// titel en samenvatting in de gekozen taal (met terugval op wat er is)
const T = (o) => o.t?.[L()] || o.title;
const S = (o) => o.s?.[L()] ?? o.summary;
// zonder "t" (één leestaal): vertaald als er een originele titel bewaard is
const isTranslated = (o) => o.lang && o.lang !== L() && Boolean(o.t ? o.t[L()] : o.orig_title);
const origTitle = (o) => (o.lang && o.lang !== L() ? o.t?.[o.lang] || o.orig_title : null);

function timeAgo(iso) {
  const min = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (min < 1) return t().justNow;
  if (min < 60) return `${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h} ${t().h}`;
  return `${Math.round(h / 24)} ${t().d}`;
}
function updatedAgo() {
  const ago = timeAgo(state.data.generated);
  return ago === t().justNow ? ago : t().ago(ago);
}
const clock = (iso) => new Date(iso).toLocaleTimeString(LOCALE[L()], { hour: "2-digit", minute: "2-digit" });

// --- data ---
async function downloadNews() {
  const res = await fetch(`data/news.json?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(res.status);
  return res.json();
}
function useNews(data) {
  state.data = data;
  // enkel talen waarin het nieuws ook vertaald is (LANGUAGES in fetcher/sources.py; standaard enkel Nederlands)
  if (!dataLangs().includes(prefs.lang)) { prefs.lang = dataLangs()[0]; applyLanguage(); }
  state.sources = Object.fromEntries(data.sources.map((s) => [s.id, s]));
  personalize();
  hideNewsBar();
}

// --- personaliseren: welke verhalen, onder welke rubriek, in welke volgorde ---
function personalize() {
  if (!state.data) return;
  const off = new Set(prefs.off);
  const star = new Set(prefs.star);
  const boosts = state.data.boosts || {};
  const boostOf = (id) => (boosts[id] || 1) * (star.has(id) ? STAR_BOOST : 1);
  const out = [];
  for (const story of state.data.stories) {
    const secs = story.sections.filter((s) => !off.has(s) && THEME[s]);
    if (!secs.length) continue; // valt volledig buiten je rubrieken
    const kicker = secs.includes(story.kicker) ? story.kicker : KICKER_ORDER.find((s) => secs.includes(s));
    // nieuws.json van vóór deze versie heeft geen "base": dan de score van de server behouden
    const score = story.base == null ? story.score : story.base * Math.max(...secs.map(boostOf));
    story.my = { sections: secs, kicker, score };
    out.push(story);
  }
  out.sort((a, b) => b.my.score - a.my.score);
  state.stories = out;
}
const dataLangs = () => (state.data?.langs?.length ? state.data.langs.filter((l) => LANGS.includes(l)) : ["nl"]);
const visibleThemes = () => THEMES.filter((x) => !prefs.off.includes(x.id));

const src = (id) => state.sources[id] || { name: id };
const sourceCount = (story) => new Set(story.articles.map((a) => a.source)).size;
const findStory = (id) => state.data.stories.find((s) => String(s.id) === String(id));

// --- volledige teksten: versleuteld, enkel leesbaar met jouw wachtwoord ---
let textsJob = { key: null, promise: null };

async function decryptBlob(buf, password) {
  const bytes = new Uint8Array(buf);
  if (String.fromCharCode(...bytes.slice(0, 3)) !== "FM1") throw new Error("onbekend formaat");
  const salt = bytes.slice(3, 19), iv = bytes.slice(19, 31), data = bytes.slice(31);
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(password), "PBKDF2", false, ["deriveKey"]);
  const key = await crypto.subtle.deriveKey(
    { name: "PBKDF2", salt, iterations: PBKDF2_ITERATIONS, hash: "SHA-256" },
    base, { name: "AES-GCM", length: 256 }, false, ["decrypt"]
  );
  const plain = await crypto.subtle.decrypt({ name: "AES-GCM", iv }, key, data);
  const stream = new Blob([plain]).stream().pipeThrough(new DecompressionStream("gzip"));
  return JSON.parse(await new Response(stream).text());
}

function ensureTexts() {
  const key = `${state.data.generated}|${state.password}`;
  if (textsJob.key !== key) {
    const job = {
      key,
      promise: fetch(`data/texts.bin?t=${encodeURIComponent(state.data.generated)}`)
        .then((r) => { if (!r.ok) throw new Error("niet gevonden"); return r.arrayBuffer(); })
        .then((buf) => decryptBlob(buf, state.password)),
    };
    job.promise.catch(() => { if (textsJob === job) textsJob = { key: null, promise: null }; });
    textsJob = job;
  }
  return textsJob.promise;
}

// oud formaat ({p: [...], o, s: [...]}) en nieuw formaat ({l, o, p: {taal: [...]}, s: {taal: [...]}}) gelijk behandelen
function normalizeEntry(entry, a) {
  if (Array.isArray(entry.p)) return { l: a.lang || "nl", o: entry.o || entry.p, p: { nl: entry.p }, s: { nl: entry.s || [] } };
  return entry;
}

// --- bouwstenen ---
function leanBar(leans, cls = "bar") {
  const total = LEANS.reduce((n, l) => n + (leans[l] || 0), 0);
  if (!total) return "";
  const parts = LEANS.filter((l) => leans[l]).map((l) => `<span style="width:${(leans[l] / total) * 100}%;background:var(--${l})"></span>`);
  return `<span class="${cls}">${parts.join("")}</span>`;
}
const leanChip = (l) => (l ? `<span class="lean ${l}" style="background:var(--${l})">${t().leans[l]}</span>` : "");

function imageHtml(url, name) {
  const ph = `<span class="ph">${esc((name || "?")[0])}</span>`;
  if (!url) return `<div class="img">${ph}</div>`;
  return `<div class="img">${ph}<img src="${esc(url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()"></div>`;
}

function blindText(b) { return b === "left" || b === "vooral links" ? t().blindLeft : b === "right" || b === "vooral rechts" ? t().blindRight : b; }

function kickerHtml(story, withSection = state.tab === "voorjou") {
  const tags = [];
  const sec = story.my?.kicker;
  if (sec && withSection && THEME[sec]) tags.push(`<span class="tag" style="--c:${themeColor(sec)}">${esc(themeName(sec))}</span>`);
  if (story.blindspot) tags.push(`<span class="tag blind">${t().blind} · ${esc(blindText(story.blindspot))}</span>`);
  return tags.length ? `<div class="kicker">${tags.join("")}</div>` : "";
}

function metaHtml(story) {
  const s = src(story.source);
  const country = s.kind === "world" && s.country ? ` · ${esc(regionName(s.country))}` : "";
  const lang = isTranslated(story) ? `<span class="lang" title="${esc(t().autoTr)}">${esc(story.lang.toUpperCase())}→${L().toUpperCase()}</span>` : "";
  const n = sourceCount(story);
  const more = n > 1 ? `<span class="count">${leanBar(story.leans)}${t().nSources(n)}</span>` : "";
  return `<div class="meta"><span class="src">${esc(s.name)}</span><span>${timeAgo(story.published)}${country}</span>${lang}${more}</div>`;
}

const link = (story, cls, inner) =>
  `<a class="${cls}${state.read.has(story.id) ? " read" : ""}" href="#lees/${story.id}" data-id="${story.id}">${inner}</a>`;

const leadCard = (s) => link(s, "lead", `${imageHtml(s.image, src(s.source).name)}<div class="pad">${kickerHtml(s)}<h2>${esc(T(s))}</h2>${S(s) ? `<p>${esc(S(s))}</p>` : ""}${metaHtml(s)}</div>`);
const gridCard = (s) => link(s, "card", `${imageHtml(s.image, src(s.source).name)}${kickerHtml(s)}<h3>${esc(T(s))}</h3>${metaHtml(s)}`);
const midCard = (s) => link(s, "mid", `${imageHtml(s.image, src(s.source).name)}${kickerHtml(s, false)}<h3>${esc(T(s))}</h3>${metaHtml(s)}`);
const rowCard = (s, withSection) => link(s, s.image ? "row" : "row noimg", `<div>${kickerHtml(s, withSection)}<h3>${esc(T(s))}</h3>${metaHtml(s)}</div>${s.image ? imageHtml(s.image, src(s.source).name) : ""}`);
const rankCard = (s, i) => link(s, "rank", `<span class="n">${i}</span><div><h3>${esc(T(s))}</h3>${metaHtml(s)}</div>${imageHtml(s.image, src(s.source).name)}`);
const latestCard = (s) => link(s, "latest", `<time>${clock(s.published)}</time><div><h3>${esc(T(s))}</h3><div class="meta"><span class="src">${esc(src(s.source).name)}</span></div></div>`);

function block(title, sub, inner, sec) {
  const color = sec ? ` style="--c:${themeColor(sec)}"` : "";
  const more = sec ? `<button data-goto="${sec}">${t().all}</button>` : "";
  return `<section class="block"><div class="block-head"${color}><h2>${title}${sub ? `<small>${sub}</small>` : ""}</h2>${more}</div>${inner}</section>`;
}

// --- voorpagina ---
function dateline() {
  const today = new Date().toLocaleDateString(LOCALE[L()], { weekday: "long", day: "numeric", month: "long" });
  return `<div class="dateline"><b>${today[0].toUpperCase() + today.slice(1)}</b><span>${t().updated(updatedAgo())}</span></div>`;
}

function picker(used) {
  return (list, n) => {
    const out = [];
    for (const s of list) {
      if (out.length >= n) break;
      if (!used.has(s.id)) { used.add(s.id); out.push(s); }
    }
    return out;
  };
}

function renderHome() {
  const all = state.stories;
  if (!all.length) { feed.innerHTML = dateline() + `<p class="status">${t().emptyAll}</p>`; return; }
  const used = new Set();
  const take = picker(used);
  const withImg = all.filter((s) => s.image);
  const [lead] = take(withImg.length ? withImg : all, 1);
  const top = take(withImg, 4);
  let html = dateline() + (lead ? leadCard(lead) : "") + (top.length ? `<div class="grid">${top.map(gridCard).join("")}</div>` : "");

  const broad = take([...all].filter((s) => sourceCount(s) >= 3).sort((a, b) => sourceCount(b) - sourceCount(a) || b.my.score - a.my.score), 5);
  if (broad.length) html += block(t().broad, t().broadSub, broad.map((s, i) => rankCard(s, i + 1)).join(""));

  for (const th of visibleThemes()) {
    const list = take(all.filter((s) => s.my.sections.includes(th.id)), 4);
    if (!list.length) continue;
    const first = list[0].image ? midCard(list[0]) : rowCard(list[0], false);
    html += block(esc(themeBlock(th.id)), "", first + list.slice(1).map((s) => rowCard(s, false)).join(""), th.id);
  }

  const latest = take([...all].sort((a, b) => b.published.localeCompare(a.published)), 8);
  if (latest.length) html += block(t().latest, "", latest.map(latestCard).join(""));
  html += block(t().more, "", "");

  feed.innerHTML = html + `<div id="more-list"></div>`;
  state.list = all.filter((s) => !used.has(s.id));
  state.shown = 0;
  renderMore();
}

function renderSection() {
  const all = state.stories.filter((s) => s.my.sections.includes(state.tab));
  if (!all.length) { feed.innerHTML = `<p class="status">${t().emptyTheme}</p>`; return; }
  const used = new Set();
  const take = picker(used);
  const withImg = all.filter((s) => s.image);
  const [lead] = take(withImg.length ? withImg : all, 1);
  const top = take(withImg, 4);
  feed.innerHTML = dateline() + leadCard(lead) + (top.length ? `<div class="grid">${top.map(gridCard).join("")}</div>` : "") + `<div id="more-list"></div>`;
  state.list = all.filter((s) => !used.has(s.id));
  state.shown = 0;
  renderMore();
}

function renderMore() {
  const box = document.getElementById("more-list");
  if (!box) return;
  document.getElementById("sentinel")?.remove();
  const next = state.list.slice(state.shown, state.shown + PAGE_SIZE);
  state.shown += next.length;
  box.insertAdjacentHTML("beforeend", next.map((s) => rowCard(s)).join(""));
  if (state.shown < state.list.length) {
    box.insertAdjacentHTML("beforeend", `<div id="sentinel" style="height:1px"></div>`);
    observer.observe(document.getElementById("sentinel"));
  } else {
    box.insertAdjacentHTML("beforeend", `<div class="end"><strong>${t().endTitle}</strong>${t().endText(state.data.rules?.max_age_h || 36)}</div>`);
  }
}

const observer = new IntersectionObserver((entries) => {
  if (entries.some((e) => e.isIntersecting)) renderMore();
}, { rootMargin: "800px" });

// --- instellingen ---
function renderSettings() {
  const tr = t();
  const themes = THEMES.map((x) => {
    const on = !prefs.off.includes(x.id), starred = prefs.star.includes(x.id);
    return `<li class="opt" style="--c:${x.color}">
      <label><input type="checkbox" data-theme-on="${x.id}"${on ? " checked" : ""}><i></i><span>${esc(themeBlock(x.id))}</span></label>
      <button class="star${starred ? " on" : ""}" data-star="${x.id}" aria-pressed="${starred}" title="${esc(tr.sStar)}" aria-label="${esc(tr.sStar)}: ${esc(themeName(x.id))}"${on ? "" : " disabled"}>★</button>
    </li>`;
  }).join("");
  feed.innerHTML = `<section class="page settings">
    <h2>${tr.sTitle}</h2>
    <p class="why">${tr.sIntro}</p>

    ${dataLangs().length > 1 ? `<h3>${tr.sLang}</h3>
    <p class="help">${tr.sLangHelp}</p>
    <div class="seg" role="group" aria-label="${esc(tr.sLang)}">${dataLangs().map((l) => `<button data-lang="${l}" aria-pressed="${l === L()}"${l === L() ? ' class="on"' : ""}>${{ nl: "Nederlands", fr: "Français", en: "English" }[l]}</button>`).join("")}</div>` : ""}

    <h3>${tr.sThemes}</h3>
    <p class="help">${tr.sThemesHelp}</p>
    <ul class="opts">${themes}</ul>

    <div class="actions">
      <button class="btn ghost" id="prefs-reset">${tr.sReset}</button>
      ${state.password ? `<p class="help">${tr.sPwSaved}</p><button class="btn ghost" id="forget-pw">${tr.sLock}</button>` : ""}
    </div>
  </section>`;
}

function changePrefs(fn) {
  fn();
  savePrefs();
  personalize();
  buildTabs();
  const y = window.scrollY;
  renderSettings();
  window.scrollTo(0, y);
}

feed.addEventListener("change", (e) => {
  const el = e.target;
  if (!el.dataset.themeOn) return;
  changePrefs(() => {
    const off = new Set(prefs.off);
    el.checked ? off.delete(el.dataset.themeOn) : off.add(el.dataset.themeOn);
    prefs.off = [...off];
  });
});

function applyLanguage() {
  document.documentElement.lang = L();
  document.querySelectorAll("[data-i18n]").forEach((el) => { el.textContent = t()[el.dataset.i18n]; });
  document.querySelectorAll("[data-i18n-label]").forEach((el) => { el.setAttribute("aria-label", t()[el.dataset.i18nLabel]); el.title = t()[el.dataset.i18nLabel]; });
}

// --- bronnenpagina ---
function renderSources() {
  const d = state.data, tr = t();
  const textStats = {};
  for (const s of d.stories) for (const a of s.articles) {
    const x = (textStats[a.source] ||= { text: 0, all: 0 });
    x.all++;
    if (a.text) x.text++;
  }
  const lists = Object.entries(tr.groups).map(([kind, name]) => {
    const list = d.sources.filter((s) => s.kind === kind);
    if (!list.length) return "";
    const rows = list.map((s) => {
      const where = s.kind === "world" && s.country ? `<span class="badge">${esc(regionName(s.country))}</span>` : "";
      const x = textStats[s.id];
      const status = !s.ok ? `<span class="n err">${tr.unreachable}</span>`
        : x && x.text / x.all >= 0.3 ? `<span class="n">${tr.textInApp}</span>` : `<span class="n">${tr.linkOnly}</span>`;
      return `<li>${esc(s.name)} ${leanChip(s.lean)}${where}${status}</li>`;
    });
    return `<h2>${name}</h2><ul class="srclist">${rows.join("")}</ul>`;
  });
  const bold = (txt) => txt.replace(/^([^.]+\.)/, "<b>$1</b>");
  feed.innerHTML = `<section class="page">
    <h2>${tr.aboutTitle}</h2>
    <p>${tr.about(d.sources.length)}</p>
    <p>${bold(tr.aboutNeutral)}</p>
    <p>${bold(tr.aboutRead)}</p>
    <p>${bold(tr.aboutTranslate)}</p>
    <p>${tr.aboutBlind}</p>
    <div class="legend">${LEANS.map((l) => `<span><i style="background:var(--${l})"></i>${tr.leans[l]}</span>`).join("")}</div>
    ${lists.join("")}
    <h2>${tr.blockedTitle}</h2>
    <p>${tr.blockedText}</p>
    <div class="blocked">${(d.rules?.blocked || []).map((b) => `<span>${esc(b)}</span>`).join("")}</div>
  </section>`;
}

function render() {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
  document.getElementById("open-settings").classList.toggle("active", state.tab === "instellingen");
  if (!state.data) return;
  if (state.tab === "bronnen") renderSources();
  else if (state.tab === "instellingen") renderSettings();
  else if (state.tab === "voorjou") renderHome();
  else renderSection();
}

// --- leesweergave ---
function whyPickText(list) {
  const w = t().why;
  return (list || []).map((x) => {
    if (typeof x === "string") return x; // oud formaat
    const [code, n] = x;
    if (code === "found") return w.found;
    if (code === "text") return w.text;
    if (code === "loaded") return n ? w.loaded(n) : w.loaded0;
    if (code === "others") return w.others(n);
    if (code.startsWith("lean_")) return w.lean[code.slice(5)] || "";
    return "";
  }).filter(Boolean).map((s, i) => (i === 0 ? s[0].toUpperCase() + s.slice(1) : s)).join(" · ");
}

function versionHtml(story, a, i, current) {
  const s = src(a.source), tr = t();
  const tone = a.loaded.length
    ? `${tr.loadedWords} <b>${a.loaded.map(esc).join(", ")}</b>`
    : a.text ? tr.noLoaded : tr.notMeasured;
  const badges = [
    i === 0 && story.articles.length > 1 ? `<span class="badge good">${tr.bMostNeutral}</span>` : "",
    a.found ? `<span class="badge">${tr.bFound}</span>` : "",
    a.opinion ? `<span class="badge">${tr.bOpinion}</span>` : "",
    a.live ? `<span class="badge">${tr.bLive}</span>` : "",
    a.text ? `<span class="badge">${tr.bText}</span>` : `<span class="badge">${tr.bLink}</span>`,
  ].join(" ");
  const orig = isTranslated(a) ? origTitle(a) : null;
  return `<button class="version${current ? " current" : ""}" data-version="${i}" style="--lc:var(--${s.lean || "line"})">
    <div class="meta"><span class="src">${esc(s.name)}</span>${leanChip(s.lean)}<span>${timeAgo(a.published)}</span></div>
    <div class="t">${esc(T(a))}</div>
    ${orig ? `<div class="o">${esc(orig)}</div>` : ""}
    <div class="tone">${tone}</div>
    <div class="meta">${badges}</div>
  </button>`;
}

function readerHtml(story, a, idx) {
  const s = src(a.source), tr = t();
  const lang = a.lang && a.lang !== L() ? `<span class="lang">${esc(tr.translatedFrom(langName(a.lang)))}</span>` : "";
  const n = story.articles.length;
  const pick = n > 1
    ? idx === 0
      ? `<div class="pick"><strong>${tr.mostNeutralOf(n)}</strong>${esc(whyPickText(story.why_pick))}</div>`
      : `<div class="pick"><strong>${esc(tr.youRead(s.name))}</strong>${esc(tr.neutralFrom(src(story.articles[0].source).name))} <a href="#" data-version="0">${tr.readThat}</a></div>`
    : "";
  const versions = n > 1 ? `<section class="compare">
      <h2>${tr.compareTitle(n)}</h2>
      <p>${tr.compareText}</p>
      ${leanBar(story.leans, "spectrum")}
      <div class="legend">${LEANS.filter((l) => story.leans[l]).map((l) => `<span><i style="background:var(--${l})"></i>${tr.leans[l]}: ${story.leans[l]}</span>`).join("")}</div>
      ${story.articles.map((x, i) => versionHtml(story, x, i, i === idx)).join("")}
    </section>` : `<section class="compare"><h2>${tr.oneSource}</h2><p>${esc(tr.onlyOne(s.name))}</p>${a.loaded.length ? `<p>${tr.loadedIn} ${a.loaded.map(esc).join(", ")}</p>` : ""}</section>`;
  const image = a.image || (idx === 0 ? story.image : "");
  const orig = isTranslated(a) ? origTitle(a) : null;

  return `<div class="reader-bar">
      <button class="icon-btn" id="reader-back" aria-label="${esc(tr.back)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      <span class="who">${esc(s.name)}</span>
      <a class="icon-btn" href="${esc(a.link)}" target="_blank" rel="noopener" aria-label="${esc(tr.readAtShort(s.name))}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
    </div>
    <article class="article">
      ${kickerHtml(story, true)}
      <h1>${esc(T(a))}</h1>
      ${orig ? `<p class="orig">${esc(orig)}</p>` : ""}
      <div class="byline"><b>${esc(s.name)}</b>${leanChip(s.lean)}<span>${clock(a.published)} · ${t().ago(timeAgo(a.published))}</span>${lang}</div>
      ${image ? `<figure>${imageHtml(image, s.name)}</figure>` : ""}
      ${pick}
      <div class="body" id="r-body"></div>
      <a class="source-link" href="${esc(a.link)}" target="_blank" rel="noopener">${esc(tr.origAt(s.name))}</a>
    </article>
    ${versions}`;
}

function paragraphsHtml(paras) {
  // korte regels zonder leesteken op het einde zijn tussentitels
  return paras.map((p) => (p.length < 90 && !/[.!?:;"”'’)]$/.test(p) ? `<h3>${esc(p)}</h3>` : `<p>${esc(p)}</p>`)).join("");
}

function noTextHtml(story, a) {
  const s = src(a.source), tr = t();
  const reason = tr.noText[a.why] ? esc(tr.noTextWhy(s.name, tr.noText[a.why])) : tr.noTextAny;
  const alt = story.articles.findIndex((x) => x.text);
  return `<div class="box">
    ${S(a) ? `<p>${esc(S(a))}</p>` : ""}
    <p class="why">${reason}</p>
    <a class="btn" href="${esc(a.link)}" target="_blank" rel="noopener">${esc(tr.readAt(s.name))}</a>
    ${alt >= 0 ? `<button class="btn ghost" data-version="${alt}">${esc(tr.readAtShort(src(story.articles[alt].source).name))}</button>` : ""}
  </div>`;
}

function lockHtml(error) {
  const tr = t();
  return `<form class="box" id="pw-form">
    <p><b>${tr.pwTitle}</b></p>
    <p class="why">${tr.pwWhy}</p>
    <input type="text" name="username" value="Feed Me" autocomplete="username" hidden>
    <input type="password" id="pw-input" name="password" autocomplete="current-password" placeholder="${esc(tr.password)}" aria-label="${esc(tr.password)}" required>
    ${error ? `<p class="err">${esc(error)}</p>` : ""}
    <button class="btn" type="submit">${tr.open}</button>
  </form>`;
}

async function fillBody(story, a) {
  const body = document.getElementById("r-body");
  if (!body) return;
  if (!a.text || !state.data.texts) { body.innerHTML = noTextHtml(story, a.text ? { ...a, why: null } : a); return; }
  if (!state.password) { body.innerHTML = lockHtml(); return; }
  body.innerHTML = `<p class="loading">${t().articleLoading}</p>`;
  try {
    const texts = await ensureTexts();
    if (document.getElementById("r-body") !== body) return; // intussen ander artikel geopend
    const raw = texts[String(a.id)];
    if (!raw) { body.innerHTML = noTextHtml(story, { ...a, why: null }); return; }
    const entry = normalizeEntry(raw, a);
    const tr = t();
    const has = Boolean(entry.p[L()]);
    const foreign = entry.l !== L();
    const paras = (state.showOriginal && foreign) || !has ? entry.o : entry.p[L()];
    const bullets = has && entry.s?.[L()]?.length
      ? `<div class="summary"><h2>${tr.summary}</h2><ul>${entry.s[L()].map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
         <p class="note">${tr.summaryNote}</p></div>`
      : "";
    body.innerHTML = bullets +
      (foreign && has ? `<button class="toggle" id="toggle-orig">${state.showOriginal ? tr.showTr : tr.showOrig}</button>` : "") +
      (foreign && !has ? `<p class="note">${tr.untranslated}</p>` : "") +
      paragraphsHtml(paras);
  } catch (e) {
    if (e && e.name === "OperationError") {
      state.password = null;
      save("pw", null);
      body.innerHTML = lockHtml(t().wrongPw);
    } else body.innerHTML = `<div class="box"><p class="why">${t().articlesFail}</p><a class="btn" href="${esc(a.link)}" target="_blank" rel="noopener">${esc(t().readAt(src(a.source).name))}</a></div>`;
  }
}

function openReader(id, idx) {
  const story = findStory(id);
  if (!story) { closeReader(); return; }
  const i = story.articles[idx] ? idx : 0;
  const a = story.articles[i];
  state.read.add(story.id);
  save("read", [...state.read].slice(-500));
  feed.querySelectorAll(`[data-id="${story.id}"]`).forEach((el) => el.classList.add("read"));
  reader.innerHTML = readerHtml(story, a, i);
  reader.hidden = false;
  reader.scrollTop = 0;
  document.body.classList.add("reading");
  document.title = `${T(a)} · Feed Me`;
  reader.dataset.story = story.id;
  reader.dataset.idx = i;
  fillBody(story, a);
}

function closeReader() {
  if (reader.hidden) return;
  reader.hidden = true;
  reader.innerHTML = "";
  document.body.classList.remove("reading");
  document.title = "Feed Me";
}

function route() {
  const m = location.hash.match(/^#lees\/(\d+)(?:\/(\d+))?/);
  if (m && state.data) openReader(m[1], Number(m[2] || 0));
  else closeReader();
}

// --- tabs: Voor jou, dan je thema's, dan Bronnen ---
function buildTabs() {
  const nav = document.getElementById("tabs");
  nav.querySelectorAll("[data-theme]").forEach((b) => b.remove());
  const last = nav.querySelector('[data-tab="bronnen"]');
  for (const x of visibleThemes()) {
    const b = document.createElement("button");
    b.dataset.tab = x.id;
    b.dataset.theme = "";
    b.style.setProperty("--c", x.color);
    b.textContent = themeName(x.id);
    nav.insertBefore(b, last);
  }
  if (!["voorjou", "bronnen", "instellingen"].includes(state.tab) && !visibleThemes().some((x) => x.id === state.tab)) state.tab = "voorjou";
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
}

// --- events ---
document.getElementById("tabs").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-tab]");
  if (btn) switchTab(btn.dataset.tab);
});
document.getElementById("open-settings").addEventListener("click", () => switchTab(state.tab === "instellingen" ? "voorjou" : "instellingen"));

function switchTab(tab) {
  state.tab = tab;
  save("tab", state.tab);
  render();
  window.scrollTo({ top: 0 });
  document.querySelector(`#tabs button[data-tab="${tab}"]`)?.scrollIntoView({ inline: "center", block: "nearest" });
}

document.querySelector(".brand").addEventListener("click", (e) => {
  e.preventDefault();
  switchTab("voorjou");
});

feed.addEventListener("click", (e) => {
  const goto = e.target.closest("[data-goto]");
  if (goto) { switchTab(goto.dataset.goto); return; }
  if (e.target.closest("[data-id]")) state.fromFeed = true;
  if (e.target.closest("#forget-pw")) {
    state.password = null;
    save("pw", null);
    render();
    return;
  }
  const lang = e.target.closest("[data-lang]");
  if (lang) {
    changePrefs(() => { prefs.lang = lang.dataset.lang; });
    applyLanguage();
    return;
  }
  const star = e.target.closest("[data-star]");
  if (star) {
    changePrefs(() => {
      const st = new Set(prefs.star);
      st.has(star.dataset.star) ? st.delete(star.dataset.star) : st.add(star.dataset.star);
      prefs.star = [...st];
    });
    return;
  }
  if (e.target.closest("#prefs-reset")) {
    changePrefs(() => { prefs = defaultPrefs(); });
    applyLanguage();
  }
});

reader.addEventListener("click", (e) => {
  if (e.target.closest("#reader-back")) {
    if (state.fromFeed) history.back();
    else location.replace("#");
    return;
  }
  const v = e.target.closest("[data-version]");
  if (v) {
    e.preventDefault();
    location.replace(`#lees/${reader.dataset.story}/${v.dataset.version}`);
    return;
  }
  if (e.target.closest("#toggle-orig")) {
    state.showOriginal = !state.showOriginal;
    const story = findStory(reader.dataset.story);
    fillBody(story, story.articles[Number(reader.dataset.idx)]);
  }
});

reader.addEventListener("submit", (e) => {
  if (e.target.id !== "pw-form") return;
  e.preventDefault();
  state.password = document.getElementById("pw-input").value.trim();
  save("pw", state.password);
  const story = findStory(reader.dataset.story);
  fillBody(story, story.articles[Number(reader.dataset.idx)]);
});

window.addEventListener("hashchange", () => {
  if (!location.hash.startsWith("#lees/")) state.fromFeed = false;
  route();
});

// --- vernieuwen: de pagina verandert enkel als jij erop tikt ---
const refreshBtn = document.getElementById("refresh");
const newsBar = document.getElementById("newsbar");
let pending = null, lastCheck = Date.now(), toastTimer;

function toast(text) {
  const el = document.getElementById("toast");
  el.textContent = text;
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { el.hidden = true; }, 3500);
}
function hideNewsBar() { pending = null; newsBar.hidden = true; }
function showNews(data) {
  useNews(data);
  render();
  if (!location.hash.startsWith("#lees/")) window.scrollTo(0, 0);
  if (state.password && state.data.texts) ensureTexts().catch(() => {});
}
const ageMin = () => (Date.now() - new Date(state.data.generated)) / 60000;

// --- zelf een update starten bij GitHub (GitHub slaat zijn eigen planning vaak urenlang over) ---
const REPO = "JosCiv7/feed-me";
const UPDATE_MIN = 8;  // zo lang duurt een update ongeveer
const sheet = document.getElementById("sheet");

async function github(path, token, options = {}) {
  return fetch(`https://api.github.com/repos/${REPO}${path}`, {
    ...options,
    headers: { Accept: "application/vnd.github+json", Authorization: `Bearer ${token}`, ...(options.headers || {}) },
  });
}

async function startUpdate() {
  const token = load("ghtoken", null);
  if (!token) { openSheet(); return; }
  // loopt er al een update? dan niet nog een starten, gewoon wachten
  let running = false;
  try {
    const res = await github("/actions/runs?per_page=5", token);
    if (res.status === 401 || res.status === 403) throw new Error("sleutel");
    const runs = (await res.json()).workflow_runs || [];
    running = runs.some((r) => r.status !== "completed");
  } catch (e) {
    if (e.message === "sleutel") { save("ghtoken", null); openSheet(t().ghBadKey); return; }
  }
  if (!running) {
    const res = await github("/actions/workflows/update.yml/dispatches", token, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ref: "main" }) });
    if (res.status === 401 || res.status === 403 || res.status === 404) {
      save("ghtoken", null);
      openSheet(t().ghNoRights);
      return;
    }
    if (!res.ok) throw new Error(res.status);
  }
  save("waiting", Date.now());
  toast(t().updStarted(UPDATE_MIN));
  watchUpdate();
}

// tijdens het wachten elke 30 s kijken of het nieuwe nieuws er is
let watchTimer = null;
function watchUpdate() {
  clearInterval(watchTimer);
  refreshBtn.classList.add("busy");
  watchTimer = setInterval(async () => {
    const since = load("waiting", 0);
    if (Date.now() - since > 25 * 60000) { stopWatching(); return; }
    if (document.hidden) return;
    try {
      const data = await downloadNews();
      if (data.generated > state.data.generated && new Date(data.generated) > since - 60000) { stopWatching(); offerNews(data); }
    } catch {}
  }, 30000);
}
function stopWatching() {
  clearInterval(watchTimer);
  save("waiting", 0);
  refreshBtn.classList.remove("busy");
}

function offerNews(data) {
  pending = data;
  newsBar.hidden = false;
}

function openSheet(error) {
  const tr = t();
  sheet.querySelector("form").innerHTML = `<p><b>${tr.ghTitle}</b></p>
    <p>${tr.ghIntro(UPDATE_MIN)}</p>
    <ol>${tr.ghSteps.map((x) => `<li>${x}</li>`).join("")}</ol>
    <p class="why">${tr.ghWhy}</p>
    <input type="password" autocomplete="off" placeholder="github_pat_…" aria-label="${esc(tr.ghKey)}">
    <p class="err">${esc(error || "")}</p>
    <button class="btn" type="submit">${tr.ghSave}</button><button class="btn ghost" type="button" data-close>${tr.ghLater}</button>`;
  sheet.hidden = false;
}
sheet.addEventListener("click", (e) => {
  if (e.target === sheet || e.target.closest("[data-close]")) sheet.hidden = true;
});
sheet.querySelector("form").addEventListener("submit", (e) => {
  e.preventDefault();
  const token = sheet.querySelector("input").value.trim();
  if (!token) return;
  save("ghtoken", token);
  sheet.hidden = true;
  refreshBtn.click();
});

refreshBtn.addEventListener("click", async () => {
  if (refreshBtn.classList.contains("spin") || !state.data) return;
  refreshBtn.classList.add("spin");
  try {
    const data = pending || await downloadNews();
    if (data.generated > state.data.generated) showNews(data);
    else if (load("waiting", 0)) toast(t().updWaiting);
    else if (ageMin() < 20) toast(t().latestNews(updatedAgo()));
    else await startUpdate();
  } catch {
    toast(t().refreshFail);
  }
  refreshBtn.classList.remove("spin");
});
newsBar.addEventListener("click", () => { if (pending) showNews(pending); });

// terug in de app (of elke 10 min als ze openstaat): stil nagaan of er nieuwer nieuws is en dat enkel melden
async function checkForNews() {
  if (!state.data || document.hidden || Date.now() - lastCheck < 5 * 60000) return;
  lastCheck = Date.now();
  try {
    const data = await downloadNews();
    if (data.generated > state.data.generated) offerNews(data);
  } catch {}
}
document.addEventListener("visibilitychange", checkForNews);
setInterval(checkForNews, 10 * 60000);
if (load("waiting", 0)) watchUpdate();  // na herstarten van de app verder wachten

// --- installeren als echte app: Chrome geeft dit signaal zolang de app nog niet geïnstalleerd is ---
const installBtn = document.getElementById("install");
let installPrompt = null;
window.addEventListener("beforeinstallprompt", (e) => {
  e.preventDefault();
  installPrompt = e;
  installBtn.hidden = false;
});
installBtn.addEventListener("click", async () => {
  if (!installPrompt) return;
  installPrompt.prompt();
  await installPrompt.userChoice;
  installPrompt = null;
  installBtn.hidden = true;
});
window.addEventListener("appinstalled", () => {
  installBtn.hidden = true;
  toast(t().installed);
});

// --- start ---
(async function init() {
  applyLanguage();
  state.tab = load("tab", "voorjou");
  state.read = new Set(load("read", []));
  state.password = load("pw", null);
  buildTabs();
  try {
    useNews(await downloadNews());
    render();
    route();
    // teksten alvast op de achtergrond ontsleutelen, zodat artikels meteen openen
    if (state.password && state.data.texts) ensureTexts().catch(() => {});
  } catch {
    feed.innerHTML = `<p class="status">${t().loadFail}</p>`;
  }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
