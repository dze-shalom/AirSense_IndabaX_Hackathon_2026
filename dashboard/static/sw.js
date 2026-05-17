/* AirSense Cameroon — Service Worker (PWA offline-first) */
var CACHE_NAME = 'airsense-v2';
// Derive paths from the SW's own location so this works on local dev
// (/static/sw.js) and Streamlit Cloud (/app/static/sw.js) without changes.
var _BASE = self.location.pathname.replace('sw.js', '');
var OFFLINE_URL = _BASE + 'offline.html';
var MANIFEST_URL = _BASE + 'manifest.json';
var SHELL_ASSETS = [
  '/',
  MANIFEST_URL,
  OFFLINE_URL,
];

/* ── Install: pre-cache shell assets ─────────────────────────────────────── */
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      // Cache individually so one failure doesn't block the others
      return Promise.allSettled(
        SHELL_ASSETS.map(function(url) {
          return cache.add(url).catch(function() { /* ignore */ });
        })
      );
    })
  );
  self.skipWaiting();
});

/* ── Activate: clean up old caches ───────────────────────────────────────── */
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames
          .filter(function(name) { return name !== CACHE_NAME; })
          .map(function(name) { return caches.delete(name); })
      );
    })
  );
  self.clients.claim();
});

/* ── Fetch: network-first for navigation, cache-first for assets ─────────── */
self.addEventListener('fetch', function(event) {
  var req = event.request;

  // Only handle GET requests
  if (req.method !== 'GET') return;

  // Skip cross-origin requests (analytics, CDN fonts, etc.)
  if (!req.url.startsWith(self.location.origin)) return;

  if (req.mode === 'navigate') {
    // Navigation: try network first, then cached page, then offline fallback
    event.respondWith(
      fetch(req).then(function(response) {
        var respClone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(req, respClone);
        });
        return response;
      }).catch(function() {
        return caches.match(req).then(function(cached) {
          if (cached) return cached;
          return caches.match(OFFLINE_URL);
        });
      })
    );
  } else {
    // Assets: cache-first, network fallback
    event.respondWith(
      caches.match(req).then(function(cached) {
        if (cached) return cached;
        return fetch(req).then(function(response) {
          if (!response || response.status !== 200 || response.type === 'opaque') {
            return response;
          }
          var respClone = response.clone();
          caches.open(CACHE_NAME).then(function(cache) {
            cache.put(req, respClone);
          });
          return response;
        }).catch(function() {
          // Static asset unavailable offline — nothing to serve
          return new Response('', { status: 503, statusText: 'Offline' });
        });
      })
    );
  }
});

/* ── Push notifications ───────────────────────────────────────────────────── */
self.addEventListener('push', function(event) {
  var data = { title: 'AirSense Alert', body: 'Air quality update', url: '/' };
  try { if (event.data) data = Object.assign(data, event.data.json()); } catch(e) {}
  event.waitUntil(
    self.registration.showNotification(data.title, {
      body:    data.body,
      icon:    self.location.pathname.replace('sw.js', '') + 'icon-192.png',
      badge:   self.location.pathname.replace('sw.js', '') + 'icon-192.png',
      data:    { url: data.url },
      vibrate: [200, 100, 200],
      tag:     'airsense-alert',
      renotify: true,
    })
  );
});

self.addEventListener('notificationclick', function(event) {
  event.notification.close();
  var url = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(clients.openWindow(url));
});
