const CACHE_NAME = 'celi-sovereign-v1';
const ASSETS_TO_CACHE = [
    '/',
    '/static/manifest.json',
    '/static/image.png',
    'https://cdn.tailwindcss.com' 
];

// 1. INSTALL: Force the browser to download the core "Shell" of the app
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(CACHE_NAME).then((cache) => {
            return cache.addAll(ASSETS_TO_CACHE);
        })
    );
});

// 2. ACTIVATE: Clean up old versions of the app when you update code
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => {
                if (key !== CACHE_NAME) {
                    return caches.delete(key);
                }
            }));
        })
    );
});

// 3. FETCH: The "Smart" Network Logic
self.addEventListener('fetch', (event) => {
    // For API calls (data/process), always try Network first, don't cache deeply
    if (event.request.url.includes('/api/')) {
        event.respondWith(
            fetch(event.request).catch(() => {
                // Optional: Return a JSON offline message if you wanted
                return new Response(JSON.stringify({ error: "Offline" }));
            })
        );
        return;
    }

    // For the UI (HTML, CSS, Images), use Stale-While-Revalidate
    // (Load from cache INSTANTLY, then update in background)
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
