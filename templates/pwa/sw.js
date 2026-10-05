{% load static %}const CACHE = "kosha-offline";
const OFFLINE_URL = new URL("{% url 'offline' %}", self.location).href;
// Only what the offline page needs. Signed-in pages hold financial data and
// are never cached.
const PRECACHE = [
  OFFLINE_URL,
  new URL("{% static 'css/app.css' %}", self.location).href,
  new URL("{% static 'img/mark.svg' %}", self.location).href,
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(PRECACHE)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .open(CACHE)
      .then((cache) =>
        cache.keys().then((requests) =>
          Promise.all(
            requests.filter((r) => !PRECACHE.includes(r.url)).map((r) => cache.delete(r)),
          ),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
  } else if (PRECACHE.includes(request.url)) {
    // Network first: in development static URLs aren't hashed, so a cached
    // copy would hide stylesheet changes.
    event.respondWith(fetch(request).catch(() => caches.match(request)));
  }
});
