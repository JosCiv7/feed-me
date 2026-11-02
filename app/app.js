const PAGE_SIZE = 20;
// volgorde van de blokken op de voorpagina (en voorrang voor het label boven een verhaal)
const SECTIONS = ["brussel", "belgie", "spanje", "europa", "conflicten", "economie", "tech", "wetenschap", "mobiliteit", "wereld"];
const HOME_ORDER = ["belgie", "brussel", "spanje", "europa", "conflicten", "economie", "tech", "wetenschap", "mobiliteit", "wereld"];
const BLOCK_TITLES = { economie: "Economie & werk", wetenschap: "Wetenschap & gezondheid", mobiliteit: "Mobiliteit & wonen" };
const LEANS = ["L", "CL", "C", "CR", "R"];
const LEAN_NAMES = { L: "Links", CL: "Centrum-links", C: "Centrum", CR: "Centrum-rechts", R: "Rechts" };
const SECTION_NAMES = {
  belgie: "België", brussel: "Brussel", spanje: "Spanje", europa: "Europa", conflicten: "Conflicten",
  economie: "Economie", tech: "Tech", wetenschap: "Wetenschap", mobiliteit: "Mobiliteit", wereld: "Wereld",
};
const LANG_NAMES = { en: "het Engels", fr: "het Frans", es: "het Spaans" };
const COUNTRY_NAMES = {
  BE: "België", NL: "Nederland", UA: "Oekraïne", RU: "Rusland", IL: "Israël", QA: "Qatar", FR: "Frankrijk",
  DE: "Duitsland", ES: "Spanje", GB: "VK", IN: "India", HK: "Hongkong", JP: "Japan", US: "VS", EU: "Europa",
  AFRICA: "Afrika", LATAM: "Latijns-Amerika", IT: "Italië", PL: "Polen", EE: "Estland", BALKAN: "Balkan",
  CA: "Canada", AU: "Australië", KR: "Zuid-Korea", SG: "Singapore", PH: "Filipijnen", ZA: "Zuid-Afrika", NG: "Nigeria",
};
// waarom een volledige tekst niet in de app staat
const NO_TEXT = {
  betaalmuur: "zit achter een betaalmuur",
  inlogmuur: "vraagt om in te loggen of cookies te aanvaarden",
  geweigerd: "laat geen automatische lezers toe",
  "te kort": "geeft geen volledige tekst vrij",
};
const PBKDF2_ITERATIONS = 150000; // moet gelijk zijn aan fetcher/vault.py

const state = {
  data: null, tab: "voorjou", list: [], shown: 0, sources: {}, read: new Set(),
  password: null, showOriginal: false, fromFeed: false,
};
const feed = document.getElementById("feed");
const reader = document.getElementById("reader");

// --- opslag (mag falen, bv. in privémodus) ---
function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch {}
}

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

function timeAgo(iso) {
  const min = Math.max(0, Math.round((Date.now() - new Date(iso)) / 60000));
  if (min < 1) return "zonet";
  if (min < 60) return `${min} min`;
  const h = Math.round(min / 60);
  if (h < 24) return `${h} u`;
  return `${Math.round(h / 24)} d`;
}
const clock = (iso) => new Date(iso).toLocaleTimeString("nl-BE", { hour: "2-digit", minute: "2-digit" });

// --- data ---
async function fetchNews() {
  const res = await fetch(`data/news.json?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(res.status);
  state.data = await res.json();
  state.sources = Object.fromEntries(state.data.sources.map((s) => [s.id, s]));
}

const src = (id) => state.sources[id] || { name: id };
const sourceCount = (story) => new Set(story.articles.map((a) => a.source)).size;
const sectionOf = (story) => story.kicker || SECTIONS.find((s) => story.sections.includes(s));
const findStory = (id) => state.data.stories.find((s) => String(s.id) === String(id));

// --- volledige teksten: versleuteld, enkel leesbaar met jouw wachtwoord ---
let textsJob = { key: null, promise: null };

async function decryptTexts(buf, password) {
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
        .then((buf) => decryptTexts(buf, state.password)),
    };
    job.promise.catch(() => { if (textsJob === job) textsJob = { key: null, promise: null }; });
    textsJob = job;
  }
  return textsJob.promise;
}

// --- bouwstenen ---
function leanBar(leans, cls = "bar") {
  const total = LEANS.reduce((n, l) => n + (leans[l] || 0), 0);
  if (!total) return "";
  const parts = LEANS.filter((l) => leans[l]).map((l) => `<span style="width:${(leans[l] / total) * 100}%;background:var(--${l})"></span>`);
  return `<span class="${cls}">${parts.join("")}</span>`;
}
const leanChip = (l) => (l ? `<span class="lean ${l}" style="background:var(--${l})">${LEAN_NAMES[l]}</span>` : "");

function imageHtml(url, name) {
  const ph = `<span class="ph">${esc((name || "?")[0])}</span>`;
  if (!url) return `<div class="img">${ph}</div>`;
  return `<div class="img">${ph}<img src="${esc(url)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()"></div>`;
}

function kickerHtml(story, withSection = state.tab === "voorjou") {
  const tags = [];
  const sec = sectionOf(story);
  if (sec && withSection) tags.push(`<span class="tag" style="--c:var(--sec-${sec})">${SECTION_NAMES[sec]}</span>`);
  if (story.blindspot) tags.push(`<span class="tag blind">Blinde vlek · ${esc(story.blindspot)}</span>`);
  return tags.length ? `<div class="kicker">${tags.join("")}</div>` : "";
}

function metaHtml(story) {
  const s = src(story.source);
  const country = s.kind === "world" && s.country ? ` · ${esc(COUNTRY_NAMES[s.country] || s.country)}` : "";
  const lang = story.orig_title ? `<span class="lang" title="Automatisch vertaald">${esc(story.lang.toUpperCase())}→NL</span>` : "";
  const n = sourceCount(story);
  const more = n > 1 ? `<span class="count">${leanBar(story.leans)}${n} bronnen</span>` : "";
  return `<div class="meta"><span class="src">${esc(s.name)}</span><span>${timeAgo(story.published)}${country}</span>${lang}${more}</div>`;
}

const link = (story, cls, inner) =>
  `<a class="${cls}${state.read.has(story.id) ? " read" : ""}" href="#lees/${story.id}" data-id="${story.id}">${inner}</a>`;

const leadCard = (s) => link(s, "lead", `${imageHtml(s.image, src(s.source).name)}<div class="pad">${kickerHtml(s)}<h2>${esc(s.title)}</h2>${s.summary ? `<p>${esc(s.summary)}</p>` : ""}${metaHtml(s)}</div>`);
const gridCard = (s) => link(s, "card", `${imageHtml(s.image, src(s.source).name)}${kickerHtml(s)}<h3>${esc(s.title)}</h3>${metaHtml(s)}`);
const midCard = (s) => link(s, "mid", `${imageHtml(s.image, src(s.source).name)}<h3>${esc(s.title)}</h3>${metaHtml(s)}`);
const rowCard = (s, withSection) => link(s, s.image ? "row" : "row noimg", `<div>${kickerHtml(s, withSection)}<h3>${esc(s.title)}</h3>${metaHtml(s)}</div>${s.image ? imageHtml(s.image, src(s.source).name) : ""}`);
const rankCard = (s, i) => link(s, "rank", `<span class="n">${i}</span><div><h3>${esc(s.title)}</h3>${metaHtml(s)}</div>${imageHtml(s.image, src(s.source).name)}`);
const latestCard = (s) => link(s, "latest", `<time>${clock(s.published)}</time><div><h3>${esc(s.title)}</h3><div class="meta"><span class="src">${esc(src(s.source).name)}</span></div></div>`);

function block(title, sub, inner, sec) {
  const color = sec ? ` style="--c:var(--sec-${sec})"` : "";
  const more = sec ? `<button data-goto="${sec}">Alles ›</button>` : "";
  return `<section class="block"><div class="block-head"${color}><h2>${title}${sub ? `<small>${sub}</small>` : ""}</h2>${more}</div>${inner}</section>`;
}

// --- voorpagina ---
function dateline() {
  const today = new Date().toLocaleDateString("nl-BE", { weekday: "long", day: "numeric", month: "long" });
  return `<div class="dateline"><b>${today[0].toUpperCase() + today.slice(1)}</b><span>Bijgewerkt ${timeAgo(state.data.generated)} geleden</span></div>`;
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
  const all = state.data.stories;
  const used = new Set();
  const take = picker(used);
  const withImg = all.filter((s) => s.image);
  const [lead] = take(withImg, 1);
  const top = take(withImg, 4);
  let html = dateline() + (lead ? leadCard(lead) : "") + `<div class="grid">${top.map(gridCard).join("")}</div>`;

  const broad = take([...all].filter((s) => sourceCount(s) >= 3).sort((a, b) => sourceCount(b) - sourceCount(a) || b.score - a.score), 5);
  if (broad.length) html += block("Breed gedragen", "Verhalen die door veel media gebracht worden", broad.map((s, i) => rankCard(s, i + 1)).join(""));

  for (const sec of HOME_ORDER) {
    const list = take(all.filter((s) => s.sections.includes(sec)), 4);
    if (!list.length) continue;
    const first = list[0].image ? midCard(list[0]) : rowCard(list[0], false);
    html += block(BLOCK_TITLES[sec] || SECTION_NAMES[sec], "", first + list.slice(1).map((s) => rowCard(s, false)).join(""), sec);
  }

  const latest = take([...all].sort((a, b) => b.published.localeCompare(a.published)), 8);
  html += block("Net binnen", "", latest.map(latestCard).join(""));
  html += block("Meer nieuws", "", "");

  feed.innerHTML = html + `<div id="more-list"></div>`;
  state.list = all.filter((s) => !used.has(s.id));
  state.shown = 0;
  renderMore();
}

function renderSection() {
  const all = state.data.stories.filter((s) => s.sections.includes(state.tab));
  if (!all.length) {
    feed.innerHTML = `<p class="status">Nog geen nieuws in deze rubriek.</p>`;
    return;
  }
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
    box.insertAdjacentHTML("beforeend", `<div class="end"><strong>Je bent helemaal mee.</strong>Dit was al het nieuws van de laatste 36 uur.</div>`);
  }
}

const observer = new IntersectionObserver((entries) => {
  if (entries.some((e) => e.isIntersecting)) renderMore();
}, { rootMargin: "800px" });

// --- bronnenpagina ---
function renderSources() {
  const d = state.data;
  const textStats = {};
  for (const s of d.stories) for (const a of s.articles) {
    const t = (textStats[a.source] ||= { text: 0, all: 0 });
    t.all++;
    if (a.text) t.text++;
  }
  const groups = [["be", "België"], ["brussel", "Brussel"], ["spanje", "Spanje"], ["tech", "Tech"], ["world", "Wereld & Europa"], ["web", "Gratis versies gevonden via zoeken"]];
  const lists = groups.map(([kind, name]) => {
    const list = d.sources.filter((s) => s.kind === kind);
    if (!list.length) return "";
    const rows = list.map((s) => {
      const where = s.kind === "world" ? `<span class="badge">${esc(COUNTRY_NAMES[s.country] || s.country)}</span>` : "";
      const t = textStats[s.id];
      const status = !s.ok ? `<span class="n err">niet bereikbaar</span>`
        : t && t.text / t.all >= 0.3 ? `<span class="n">tekst in de app</span>` : `<span class="n">enkel link</span>`;
      return `<li>${esc(s.name)} ${leanChip(s.lean)}${where}${status}</li>`;
    });
    return `<h2>${name}</h2><ul class="srclist">${rows.join("")}</ul>`;
  });
  feed.innerHTML = `<section class="page">
    <h2>Hoe werkt Feed Me?</h2>
    <p>Feed Me verzamelt het nieuws van ${d.sources.length} bronnen en legt artikels over hetzelfde nieuwsfeit samen. Per verhaal zie je welke media erover berichten en uit welke hoek ze komen.</p>
    <p><b>Meest neutrale versie.</b> Als meerdere media hetzelfde verhaal brengen, toont Feed Me de meest neutrale versie: liefst een centrumbron, met volledige tekst, met zo weinig mogelijk geladen woorden (zoals "schandalig", "chaos" of "slams") en geen opiniestuk. Onder elk artikel zie je hoe de andere media het brengen.</p>
    <p><b>Lezen in de app.</b> Waar de site het toelaat, staat de volledige tekst in de app. Betaal- en loginmuren worden gerespecteerd. Staat een verhaal enkel achter zo'n muur, dan zoekt Feed Me met de titel en samenvatting naar een ander medium dat hetzelfde nieuws gratis brengt. Lukt dat niet, dan krijg je een link naar de site. De teksten zijn versleuteld met je wachtwoord, zodat enkel jij ze kan lezen.</p>
    <p><b>Vertaling.</b> Franse, Spaanse en Engelse artikels worden automatisch en gratis naar het Nederlands vertaald (label <b>FR→NL</b>). De vertaling is niet perfect; het origineel kan je altijd bekijken.</p>
    <p>Een <b>blinde vlek</b> betekent dat een verhaal bijna enkel door linkse of enkel door rechtse media wordt gebracht. De politieke labels zijn een voorstel en kunnen aangepast worden in <code>fetcher/sources.py</code>.</p>
    <div class="legend">${LEANS.map((l) => `<span><i style="background:var(--${l})"></i>${LEAN_NAMES[l]}</span>`).join("")}</div>
    ${lists.join("")}
    <h2>Geweerd: sensatie & boulevard</h2>
    <p>Deze media worden nooit getoond. Ook titels met klikaas, quizzen, reclame of "deals" worden eruit gefilterd.</p>
    <div class="blocked">${(d.rules?.blocked || []).map((b) => `<span>${esc(b)}</span>`).join("")}</div>
    ${state.password ? `<h2>Wachtwoord</h2><p>Je wachtwoord voor de volledige artikels is bewaard op dit toestel.</p><button class="btn ghost" id="forget-pw">Wachtwoord vergeten op dit toestel</button>` : ""}
  </section>`;
}

function render() {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
  if (!state.data) return;
  if (state.tab === "bronnen") renderSources();
  else if (state.tab === "voorjou") renderHome();
  else renderSection();
}

// --- leesweergave ---
function versionHtml(story, a, i, current) {
  const s = src(a.source);
  const tone = a.loaded.length
    ? `Geladen woorden: <b>${a.loaded.map(esc).join(", ")}</b>`
    : a.text ? "Geen geladen woorden gevonden" : "Toon niet gemeten (geen vrije tekst)";
  const badges = [
    i === 0 && story.articles.length > 1 ? `<span class="badge good">Meest neutraal</span>` : "",
    a.found ? `<span class="badge">Gevonden via zoeken</span>` : "",
    a.opinion ? `<span class="badge">Opinie/analyse</span>` : "",
    a.live ? `<span class="badge">Liveblog</span>` : "",
    a.text ? `<span class="badge">Tekst in app</span>` : `<span class="badge">Enkel link</span>`,
  ].join(" ");
  return `<button class="version${current ? " current" : ""}" data-version="${i}" style="--lc:var(--${s.lean || "line"})">
    <div class="meta"><span class="src">${esc(s.name)}</span>${leanChip(s.lean)}<span>${timeAgo(a.published)}</span></div>
    <div class="t">${esc(a.title)}</div>
    ${a.orig_title ? `<div class="o">${esc(a.orig_title)}</div>` : ""}
    <div class="tone">${tone}</div>
    <div class="meta">${badges}</div>
  </button>`;
}

function readerHtml(story, a, idx) {
  const s = src(a.source);
  const lang = s.lang !== "nl" ? `<span class="lang">Vertaald uit ${LANG_NAMES[s.lang] || s.lang}</span>` : "";
  const n = story.articles.length;
  const pick = n > 1
    ? idx === 0
      ? `<div class="pick"><strong>Meest neutrale versie van ${n} bronnen</strong>${esc(story.why_pick.join(" · "))}</div>`
      : `<div class="pick"><strong>Je leest de versie van ${esc(s.name)}</strong>De meest neutrale versie komt van ${esc(src(story.articles[0].source).name)}. <a href="#" data-version="0">Lees die versie</a></div>`
    : "";
  const versions = n > 1 ? `<section class="compare">
      <h2>Zo brengen ${n} media dit verhaal</h2>
      <p>Vergelijk de titels en woordkeuze. Tik op een versie om ze te lezen.</p>
      ${leanBar(story.leans, "spectrum")}
      <div class="legend">${LEANS.filter((l) => story.leans[l]).map((l) => `<span><i style="background:var(--${l})"></i>${LEAN_NAMES[l]}: ${story.leans[l]}</span>`).join("")}</div>
      ${story.articles.map((x, i) => versionHtml(story, x, i, i === idx)).join("")}
    </section>` : `<section class="compare"><h2>Eén bron</h2><p>Enkel ${esc(s.name)} brengt dit verhaal (in de bronnen van Feed Me).</p>${a.loaded.length ? `<p>Geladen woorden in dit artikel: ${a.loaded.map(esc).join(", ")}</p>` : ""}</section>`;
  const image = a.image || (idx === 0 ? story.image : "");

  return `<div class="reader-bar">
      <button class="icon-btn" id="reader-back" aria-label="Terug"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>
      <span class="who">${esc(s.name)}</span>
      <a class="icon-btn" href="${esc(a.link)}" target="_blank" rel="noopener" aria-label="Open bij ${esc(s.name)}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg></a>
    </div>
    <article class="article">
      ${kickerHtml(story, true)}
      <h1>${esc(a.title)}</h1>
      ${a.orig_title ? `<p class="orig">${esc(a.orig_title)}</p>` : ""}
      <div class="byline"><b>${esc(s.name)}</b>${leanChip(s.lean)}<span>${clock(a.published)} · ${timeAgo(a.published)} geleden</span>${lang}</div>
      ${image ? `<figure>${imageHtml(image, s.name)}</figure>` : ""}
      ${pick}
      <div class="body" id="r-body"></div>
      <a class="source-link" href="${esc(a.link)}" target="_blank" rel="noopener">Origineel artikel bij ${esc(s.name)} ↗</a>
    </article>
    ${versions}`;
}

function paragraphsHtml(paras) {
  // korte regels zonder leesteken op het einde zijn tussentitels
  return paras.map((p) => (p.length < 90 && !/[.!?:;"”'’)]$/.test(p) ? `<h3>${esc(p)}</h3>` : `<p>${esc(p)}</p>`)).join("");
}

function noTextHtml(story, a) {
  const s = src(a.source);
  const reason = NO_TEXT[a.why] ? `${esc(s.name)} ${NO_TEXT[a.why]}, dus de volledige tekst staat niet in Feed Me.` : "De volledige tekst kon (nog) niet gelezen worden.";
  const alt = story.articles.findIndex((x) => x.text);
  return `<div class="box">
    ${a.summary ? `<p>${esc(a.summary)}</p>` : ""}
    <p class="why">${reason}</p>
    <a class="btn" href="${esc(a.link)}" target="_blank" rel="noopener">Lees bij ${esc(s.name)} ↗</a>
    ${alt >= 0 ? `<button class="btn ghost" data-version="${alt}">Lees bij ${esc(src(story.articles[alt].source).name)}</button>` : ""}
  </div>`;
}

function lockHtml(error) {
  return `<form class="box" id="pw-form">
    <p><b>Volledig artikel lezen</b></p>
    <p class="why">De volledige artikels zijn beveiligd met je eigen wachtwoord. Je vindt het in het bestand "Feed Me wachtwoord.txt" op je pc. Je hoeft het maar één keer in te geven.</p>
    <input type="password" id="pw-input" autocomplete="current-password" placeholder="Wachtwoord" required>
    ${error ? `<p class="err">${esc(error)}</p>` : ""}
    <button class="btn" type="submit">Openen</button>
  </form>`;
}

async function fillBody(story, a) {
  const body = document.getElementById("r-body");
  if (!body) return;
  if (!a.text) { body.innerHTML = noTextHtml(story, a); return; }
  if (!state.data.texts) { body.innerHTML = noTextHtml(story, { ...a, why: null }); return; }
  if (!state.password) { body.innerHTML = lockHtml(); return; }
  body.innerHTML = `<p class="loading">Artikel laden…</p>`;
  try {
    const texts = await ensureTexts();
    if (document.getElementById("r-body") !== body) return; // intussen ander artikel geopend
    const entry = texts[String(a.id)];
    if (!entry) { body.innerHTML = noTextHtml(story, { ...a, why: null }); return; }
    const translated = Boolean(entry.o);
    const paras = state.showOriginal && translated ? entry.o : entry.p;
    const bullets = entry.s?.length
      ? `<div class="summary"><h2>Kort samengevat</h2><ul>${entry.s.map((b) => `<li>${esc(b)}</li>`).join("")}</ul>
         <p class="note">De belangrijkste zinnen uit het artikel zelf, automatisch gekozen.</p></div>`
      : "";
    body.innerHTML = bullets +
      (translated ? `<button class="toggle" id="toggle-orig">${state.showOriginal ? "Toon vertaling" : "Toon origineel"}</button>` : "") +
      (entry.untranslated ? `<p class="note">De vertaling van dit artikel volgt bij de volgende update; hieronder de originele tekst.</p>` : "") +
      paragraphsHtml(paras);
  } catch (e) {
    if (e && e.name === "OperationError") {
      state.password = null;
      save("pw", null);
      body.innerHTML = lockHtml("Dat wachtwoord klopt niet.");
    } else {
      body.innerHTML = `<div class="box"><p class="why">De artikels konden niet geladen worden. Ben je online?</p><a class="btn" href="${esc(a.link)}" target="_blank" rel="noopener">Lees bij ${esc(src(a.source).name)} ↗</a></div>`;
    }
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
  document.title = `${a.title} · Feed Me`;
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

// --- events ---
document.getElementById("tabs").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-tab]");
  if (btn) switchTab(btn.dataset.tab);
});

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

const refreshBtn = document.getElementById("refresh");
refreshBtn.addEventListener("click", async () => {
  refreshBtn.classList.add("spin");
  try { await fetchNews(); render(); } catch { alert("Vernieuwen lukt niet. Ben je online?"); }
  refreshBtn.classList.remove("spin");
});

// --- start ---
(async function init() {
  state.tab = load("tab", "voorjou");
  state.read = new Set(load("read", []));
  state.password = load("pw", null);
  render();
  try {
    await fetchNews();
    render();
    route();
    // teksten alvast op de achtergrond ontsleutelen, zodat artikels meteen openen
    if (state.password && state.data.texts) ensureTexts().catch(() => {});
  } catch {
    feed.innerHTML = `<p class="status">Nieuws kon niet geladen worden.</p>`;
  }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
