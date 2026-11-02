const PAGE_SIZE = 25;
const LEANS = ["L", "CL", "C", "CR", "R"];
const LEAN_NAMES = { L: "Links", CL: "Centrum-links", C: "Centrum", CR: "Centrum-rechts", R: "Rechts" };
const SECTION_NAMES = { belgie: "België", brussel: "Brussel", tech: "Tech", wereld: "Wereld" };
const COUNTRY_NAMES = {
  BE: "België", NL: "Nederland", UA: "Oekraïne", RU: "Rusland", IL: "Israël", QA: "Qatar", FR: "Frankrijk",
  DE: "Duitsland", ES: "Spanje", GB: "VK", IN: "India", HK: "Hongkong", JP: "Japan", US: "VS", EU: "Europa",
  AFRICA: "Afrika", LATAM: "Latijns-Amerika",
};

const state = { data: null, tab: "voorjou", shown: 0, list: [], sources: {}, read: new Set() };
const feed = document.getElementById("feed");
const sheet = document.getElementById("sheet");

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

// --- data ---
async function fetchNews() {
  const res = await fetch(`data/news.json?t=${Date.now()}`, { cache: "no-store" });
  if (!res.ok) throw new Error(res.status);
  state.data = await res.json();
  state.sources = Object.fromEntries(state.data.sources.map((s) => [s.id, s]));
}

function storiesFor(tab) {
  const all = state.data.stories;
  if (tab === "voorjou") return all;
  return all.filter((s) => s.sections.includes(tab));
}

// --- rendering ---
function leanBar(leans, cls = "bar") {
  const total = LEANS.reduce((n, l) => n + (leans[l] || 0), 0);
  if (!total) return "";
  const parts = LEANS.filter((l) => leans[l]).map((l) => `<span style="width:${(leans[l] / total) * 100}%;background:var(--${l})"></span>`);
  return `<span class="${cls}">${parts.join("")}</span>`;
}

function imageHtml(story) {
  const src = state.sources[story.source];
  const initial = esc((src?.name || "?")[0]);
  if (!story.image) return `<div class="img"><span class="ph">${initial}</span></div>`;
  return `<div class="img"><span class="ph">${initial}</span><img src="${esc(story.image)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()"></div>`;
}

function metaHtml(story) {
  const src = state.sources[story.source] || { name: story.source };
  const country = src.kind === "world" && src.country ? ` · ${esc(COUNTRY_NAMES[src.country] || src.country)}` : "";
  const lang = story.orig_title ? `<span class="lang" title="Automatisch vertaald">${esc(story.lang.toUpperCase())} → NL</span>` : "";
  const others = story.articles.length - 1;
  const more = others > 0
    ? `<button class="more" data-more="${story.id}">${leanBar(story.leans)}+${others} ${others === 1 ? "bron" : "bronnen"}</button>`
    : "";
  return `<div class="meta"><span class="src">${esc(src.name)}</span><span>${timeAgo(story.published)}${country}</span>${lang}${more}</div>`;
}

function kickerHtml(story) {
  const tags = [];
  if (story.blindspot) tags.push(`<span class="tag blind">Blinde vlek · ${esc(story.blindspot)}</span>`);
  if (state.tab === "voorjou") {
    const sec = story.kicker || ["brussel", "belgie", "tech", "wereld"].find((s) => story.sections.includes(s));
    if (sec) tags.push(`<span class="tag">${SECTION_NAMES[sec]}</span>`);
  }
  return tags.length ? `<div class="kicker">${tags.join("")}</div>` : "";
}

function storyHtml(story, big) {
  const read = state.read.has(story.id) ? " read" : "";
  if (big) {
    return `<a class="hero${read}" href="${esc(story.link)}" target="_blank" rel="noopener" data-id="${story.id}">
      ${imageHtml(story)}
      <div class="body">${kickerHtml(story)}<h2>${esc(story.title)}</h2>
      ${story.orig_title ? `<div class="orig">Origineel: ${esc(story.orig_title)}</div>` : ""}
      ${story.summary ? `<p>${esc(story.summary)}</p>` : ""}${metaHtml(story)}</div></a>`;
  }
  return `<a class="item${read}" href="${esc(story.link)}" target="_blank" rel="noopener" data-id="${story.id}">
    <div>${kickerHtml(story)}<h3>${esc(story.title)}</h3>${metaHtml(story)}</div>${imageHtml(story)}</a>`;
}

function renderFeed() {
  state.list = storiesFor(state.tab);
  state.shown = 0;
  feed.innerHTML = `<div class="updated">Bijgewerkt ${timeAgo(state.data.generated)} geleden · ${state.list.length} verhalen</div>`;
  if (!state.list.length) {
    feed.insertAdjacentHTML("beforeend", `<p class="status">Nog geen nieuws in deze rubriek.</p>`);
    return;
  }
  renderMore();
}

function renderMore() {
  document.getElementById("sentinel")?.remove();
  const next = state.list.slice(state.shown, state.shown + PAGE_SIZE);
  const html = next.map((s, i) => storyHtml(s, (state.shown + i) % 12 === 0)).join("");
  state.shown += next.length;
  feed.insertAdjacentHTML("beforeend", html);
  if (state.shown < state.list.length) {
    feed.insertAdjacentHTML("beforeend", `<div id="sentinel" style="height:1px"></div>`);
    observer.observe(document.getElementById("sentinel"));
  } else {
    feed.insertAdjacentHTML("beforeend", `<div class="end"><strong>Je bent helemaal mee.</strong>Dit was al het nieuws van de laatste 36 uur.</div>`);
  }
}

const observer = new IntersectionObserver((entries) => {
  if (entries.some((e) => e.isIntersecting)) renderMore();
}, { rootMargin: "800px" });

function renderSources() {
  const d = state.data;
  const groups = [["be", "België"], ["brussel", "Brussel"], ["tech", "Tech"], ["world", "Wereld & Europa"]];
  const leanChip = (l) => (l ? `<span class="lean" style="background:var(--${l})">${LEAN_NAMES[l]}</span>` : "");
  const lists = groups.map(([kind, name]) => {
    const rows = d.sources.filter((s) => s.kind === kind).map((s) => {
      const where = s.kind === "world" ? ` <span class="n">${esc(COUNTRY_NAMES[s.country] || s.country)}</span>` : "";
      const n = s.ok ? `<span class="n">${s.items} art.</span>` : `<span class="n err">niet bereikbaar</span>`;
      return `<li>${esc(s.name)} ${leanChip(s.lean)}${s.kind === "world" ? where : n}</li>`;
    });
    return `<h2>${name}</h2><ul class="srclist">${rows.join("")}</ul>`;
  });
  feed.innerHTML = `<section class="page">
    <h2>Hoe werkt Feed Me?</h2>
    <p>Feed Me verzamelt titels van ${d.sources.length} bronnen en groepeert artikels over hetzelfde nieuwsfeit. Tik op <b>+bronnen</b> om te zien welke media erover berichten en uit welke hoek ze komen.</p>
    <p>Franse en Engelse titels worden automatisch en gratis naar het Nederlands vertaald (label <b>FR → NL</b>). De vertaling is niet perfect; de originele titel staat erbij.</p>
    <p>Een <b>blinde vlek</b> betekent dat een verhaal bijna enkel door linkse of enkel door rechtse media wordt gebracht.</p>
    <p>De politieke labels zijn een eerste voorstel en kunnen aangepast worden in <code>fetcher/sources.py</code>.</p>
    <div class="legend">${LEANS.map((l) => `<span><i style="background:var(--${l})"></i>${LEAN_NAMES[l]}</span>`).join("")}</div>
    ${lists.join("")}
    <h2>Geweerd: sensatie & boulevard</h2>
    <p>Deze media worden nooit getoond. Ook titels met klikaas, quizzen, reclame of "deals" worden eruit gefilterd.</p>
    <div class="blocked">${(d.rules?.blocked || []).map((b) => `<span>${esc(b)}</span>`).join("")}</div>
  </section>`;
}

function render() {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === state.tab));
  if (!state.data) return;
  if (state.tab === "bronnen") renderSources();
  else renderFeed();
}

function openSheet(id) {
  const story = state.data.stories.find((s) => String(s.id) === String(id));
  if (!story) return;
  const body = story.articles.map((a) => {
    const src = state.sources[a.source] || { name: a.source };
    const chip = src.lean ? `<span class="lean" style="background:var(--${src.lean})">${LEAN_NAMES[src.lean]}</span>` : "";
    return `<a class="art" href="${esc(a.link)}" target="_blank" rel="noopener">
      <div class="meta"><span class="src">${esc(src.name)}</span>${chip}<span>${timeAgo(a.published)}</span></div>
      <div class="t">${esc(a.title)}</div>
      ${a.orig_title ? `<div class="orig">Origineel: ${esc(a.orig_title)}</div>` : ""}</a>`;
  }).join("");
  const unlabeled = story.articles.filter((a) => !state.sources[a.source]?.lean).length;
  document.getElementById("sheet-body").innerHTML = `
    ${leanBar(story.leans, "spectrum")}
    <div class="legend">${LEANS.filter((l) => story.leans[l]).map((l) => `<span><i style="background:var(--${l})"></i>${LEAN_NAMES[l]}: ${story.leans[l]}</span>`).join("")}</div>
    ${unlabeled ? `<p class="note">${unlabeled} buitenlandse of tech-bron${unlabeled > 1 ? "nen" : ""} zonder politiek label.</p>` : ""}
    ${body}`;
  sheet.showModal();
}

// --- events ---
document.getElementById("tabs").addEventListener("click", (e) => {
  const btn = e.target.closest("button[data-tab]");
  if (!btn) return;
  state.tab = btn.dataset.tab;
  save("tab", state.tab);
  render();
  window.scrollTo({ top: 0 });
});

feed.addEventListener("click", (e) => {
  const more = e.target.closest("[data-more]");
  if (more) {
    e.preventDefault();
    openSheet(more.dataset.more);
    return;
  }
  const card = e.target.closest("[data-id]");
  if (card) {
    state.read.add(Number(card.dataset.id));
    save("read", [...state.read].slice(-500));
    card.classList.add("read");
  }
});

document.getElementById("sheet-close").addEventListener("click", () => sheet.close());
sheet.addEventListener("click", (e) => { if (e.target === sheet) sheet.close(); });

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
  render();
  try {
    await fetchNews();
    render();
  } catch {
    feed.innerHTML = `<p class="status">Nieuws kon niet geladen worden.</p>`;
  }
  if ("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(() => {});
})();
