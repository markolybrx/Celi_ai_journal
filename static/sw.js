const CACHE_NAME = 'celi-sovereign-v10.32-nuclear';
const ASSETS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/image.png',
    'https://cdn.tailwindcss.com'
];

// 1. INSTALL: Force immediate takeover
self.addEventListener('install', (event) => {
    self.skipWaiting(); // <--- NUCLEAR OPTION: Kills old broken SW immediately
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => cache.addAll(ASSETS_TO_CACHE))
    );
});

// 2. ACTIVATE: Claim clients immediately
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) return caches.delete(key);
            }));
        }).then(() => self.clients.claim()) // <--- NUCLEAR OPTION: Take control of open tabs now
    );
});

// 3. FETCH: Network First for API, Stale-While-Revalidate for Assets
self.addEventListener('fetch', (event) => {
    if (event.request.url.includes('/api/')) {
        event.respondWith(fetch(event.request).catch(() => new Response(JSON.stringify({error: "Offline"}))));
        return;
    }
    event.respondWith(
        caches.match(event.request).then((cachedResponse) => {
            const fetchPromise = fetch(event.request).then((networkResponse) => {
                caches.open(CACHE_NAME).then((cache) => {
                    cache.put(event.request, networkResponse.clone());
                });
                return networkResponse;
            });
            return cachedResponse || fetchPromise;
        })
    );
});
