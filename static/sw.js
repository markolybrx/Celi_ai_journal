const CACHE_NAME = 'celi-ai-v1.5.1';
const ASSETS_TO_CACHE = [
    '/static/manifest.json',
    '/static/image.png',
    '/static/script.js?v=1.5.1',  // Caches the specific version of your logic
    'https://cdn.tailwindcss.com' // Caches the styling engine
];

// 1. INSTALL: Cache static assets immediately
self.addEventListener('install', (event) => {
    self.skipWaiting(); // Forces this new SW to become active instantly
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// 2. ACTIVATE: Delete any cache that isn't v1.5.1 (The "Ghost Buster")
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    console.log('[SW] Clearing old cache:', key);
                    return caches.delete(key);
                }
            }));
        }).then(() => self.clients.claim()) // Take control of the page immediately
    );
});

// 3. FETCH STRATEGY
self.addEventListener('fetch', (event) => {
    
    // A. API Requests & HTML Pages: Network Only (Safe for Auth)
    // We do NOT cache the HTML pages ('/' or '/login') to ensure the 
    // authentication check (session) always happens on the server.
    if (event.request.url.includes('/api/') || 
        event.request.mode === 'navigate' || 
        event.request.destination === 'document') {
        
        event.respondWith(
            fetch(event.request).catch(() => {
                // Optional: You could return a custom offline.html here
                return new Response("You are offline.", { headers: { 'Content-Type': 'text/plain' } });
            })
        );
        return;
    }

    // B. Static Assets (Images, JS, CSS): Cache First, then Network
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            // 1. Return cache if we have it
            if (cachedResponse) {
                return cachedResponse;
            }

            // 2. Otherwise fetch from network
            return fetch(event.request).then((networkResponse) => {
                // Check if valid
                if (!networkResponse || networkResponse.status !== 200 || networkResponse.type !== 'basic') {
                    return networkResponse;
                }

                // Cache the new asset for next time
                const responseToCache = networkResponse.clone();
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, responseToCache);
                });

                return networkResponse;
            });
        })
    );
});
