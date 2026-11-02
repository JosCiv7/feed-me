// Alles eerst van het netwerk (zo komen updates meteen door); offline de laatst bewaarde versie.
const CACHE = "feedme-v5";
const SHELL = ["./", "index.html", "style.css", "app.js", "manifest.webmanifest", "icons/icon-192.png", "icons/icon-512.png"];

self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", (e) => {
  const url = new URL(e.request.url);
  if (url.origin !== location.origin || e.request.method !== "GET") return;
  // news.json en texts.bin krijgen een ?t=… mee; bewaar ze onder één vaste sleutel
  const data = url.pathname.match(/\/data\/(news\.json|texts\.bin)$/);
  const key = data ? `data/${data[1]}` : e.request;
  e.respondWith(
    // no-cache: altijd bij GitHub nagaan of er een nieuwere versie is (GitHub cachet anders 10 min)
    fetch(e.request, { cache: "no-cache" })
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(key, copy));
        }
        return res;
      })
      .catch(() => caches.match(key))
  );
});
