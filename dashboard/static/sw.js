/* AirSense Cameroon — Service Worker (PWA offline-first) */
var CACHE_NAME = 'airsense-v1';
var SHELL_ASSETS = [
  '/',
  '/manifest.json',
];

/* ── Install: cache shell assets ─────────────────────────────────────────── */
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME).then(function(cache) {
      return cache.addAll(SHELL_ASSETS);
    }).catch(function() {
      // Silently ignore cache failures (e.g. when offline at install time)
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

  if (req.mode === 'navigate') {
    // Navigation requests: try network first, fall back to cache
    event.respondWith(
      fetch(req).then(function(response) {
        // Cache a copy of the successful navigation response
        var respClone = response.clone();
        caches.open(CACHE_NAME).then(function(cache) {
          cache.put(req, respClone);
        });
        return response;
      }).catch(function() {
        return caches.match(req).then(function(cached) {
          return cached || caches.match('/');
        });
      })
    );
  } else {
    // Non-navigation (assets, API): cache-first strategy
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
        });
      })
    );
  }
});
