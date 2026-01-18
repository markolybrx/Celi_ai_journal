const CACHE_NAME = 'celi-ai-v1.2.1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/image.png',
    'https://cdn.tailwindcss.com'
];

// 1. INSTALL: Cache assets and force immediate activation
self.addEventListener('install', (event) => {
    self.skipWaiting(); // Forces this SW to become active immediately
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// 2. ACTIVATE: Clean up old caches (Ghost Buster Logic)
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    console.log('[SW] Removing old cache:', key);
                    return caches.delete(key);
                }
            }));
        }).then(() => self.clients.claim()) // Take control of all open tabs
    );
});

// 3. FETCH: Network-First for API, Cache-First for Assets
self.addEventListener('fetch', (event) => {
    // A. API Requests: Always go to network (don't cache dynamic data)
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request)
                .catch(() => {
                    // Optional: Return a safe fallback JSON if offline
                    return new Response(JSON.stringify({error: "Offline Mode"}), {
                        headers: {'Content-Type': 'application/json'}
                    });
                })
        );
        return;
    }

    // B. Static Assets (HTML, CSS, Images): Cache First, fall back to Network
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            // Return cached response if found
            if (cachedResponse) {
                return cachedResponse;
            }

            // Otherwise, fetch from network
            return fetch(event.request).then((networkResponse) => {
                // Check if valid response
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                    return networkResponse;
                }

                // Cache the new resource for next time
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });

                return networkResponse;
            });
        })
    );
});
