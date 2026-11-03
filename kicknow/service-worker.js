/* KickNow – Progressive Web App Service Worker (Offline Cache, Background Sync & Web Push) */
'use strict';

const CACHE_NAME = 'kicknow-pwa-v4';
const IS_LOCAL_HOST = /^(192\.168\.|10\.|172\.(1[6-9]|2\d|3[01])\.|127\.|localhost)|(\.(lhr\.life|localhost\.run|pinggy\.link|trycloudflare\.com|ngrok-free\.app)$)/i.test(self.location.hostname);

const APP_SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.webmanifest',
  '/css/app.css',
  '/js/data.js',
  '/js/art.js',
  '/js/app.js',
  '/assets/logo.svg',
  '/assets/icon-180.png',
  '/assets/icon-192.png',
  '/assets/icon-512.png',
  '/vendor/leaflet/leaflet.css',
  '/vendor/leaflet/leaflet.js',
  '/vendor/maplibre/maplibre-gl.css',
  '/vendor/maplibre/maplibre-gl.js',
  '/vendor/maplibre/kicknow-style.js'
];

self.addEventListener('install', event => {
  if (IS_LOCAL_HOST) {
    self.skipWaiting();
    return;
  }
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(APP_SHELL_ASSETS).catch(() => {}))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  if (IS_LOCAL_HOST) {
    event.waitUntil(
      caches.keys()
        .then(keys => Promise.all(keys.map(k => caches.delete(k))))
        .then(() => self.registration.unregister())
        .then(() => self.clients.matchAll({ type: 'window' }))
        .then(clients => {
          clients.forEach(client => {
            if ('navigate' in client) client.navigate(client.url).catch(() => {});
          });
        })
    );
    return;
  }
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
    ).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  if (IS_LOCAL_HOST) {
    return;
  }
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);

  // Network-first with offline cache fallback for API endpoints
  if (url.pathname.startsWith('/api/v1/')) {
    event.respondWith(
      fetch(req)
        .then(res => {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Cache-first with network fallback for static app shell assets
  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then(cached => {
      if (cached) return cached;
      return fetch(req).then(res => {
        if (res && res.status === 200 && url.origin === self.location.origin) {
          const clone = res.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(req, clone));
        }
        return res;
      });
    })
  );
});

self.addEventListener('sync', event => {
  if (event.tag === 'kicknow-sync-bookings') {
    event.waitUntil(Promise.resolve());
  }
});

self.addEventListener('push', event => {
  let payload = {
    title: 'KickNow – Spiel-Erinnerung',
    body: 'Dein Fußballspiel startet in Kürze!',
    icon: '/assets/icon-192.png',
    badge: '/assets/icon-180.png',
    data: { url: '/' }
  };
  if (event.data) {
    try {
      Object.assign(payload, event.data.json());
    } catch (_) {
      payload.body = event.data.text();
    }
  }
  event.waitUntil(
    self.registration.showNotification(payload.title, {
      body: payload.body,
      icon: payload.icon,
      badge: payload.badge,
      data: payload.data
    })
  );
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const targetUrl = (event.notification.data && event.notification.data.url) || '/';
  event.waitUntil(
    self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(windowClients => {
      for (const client of windowClients) {
        if (client.url.includes(targetUrl) && 'focus' in client) {
          return client.focus();
        }
      }
      if (self.clients.openWindow) {
        return self.clients.openWindow(targetUrl);
      }
    })
  );
});
