const CACHE_NAME = 'wecare-v2';
const urlsToCache = [
  '/',
  '/static/db.js',
  '/static/api.js',
  '/static/app.js',
  '/manifest.json'
];

// Install service worker
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(urlsToCache))
  );

  // Activate updated SW ASAP
  self.skipWaiting();
});

// Fetch with stale-while-revalidate for app assets
self.addEventListener('fetch', event => {
  // Never cache API calls
  if (event.request.url.includes('/api/')) {
    event.respondWith(fetch(event.request));
    return;
  }

  event.respondWith(
    caches.match(event.request).then(cachedResponse => {
      const fetchPromise = fetch(event.request)
        .then(networkResponse => {
          // Update cache for same-origin GET requests
          if (event.request.method === 'GET') {
            const responseToCache = networkResponse.clone();
            caches.open(CACHE_NAME).then(cache => {
              cache.put(event.request, responseToCache);
            });
          }
          return networkResponse;
        })
        .catch(() => cachedResponse || new Response('Offline'));

      // Serve cache immediately if present, update in background
      return cachedResponse || fetchPromise;
    })
  );
});

// Clean up old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(cacheName => cacheName !== CACHE_NAME)
          .map(cacheName => caches.delete(cacheName))
      );
    })
  );

  // Take control of pages immediately
  self.clients.claim();
});
