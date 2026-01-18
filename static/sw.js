// KILL SWITCH: Forces the browser to discard old caches and use the network
self.addEventListener('install', (event) => {
    self.skipWaiting(); // Immediately replace the old Service Worker
});

self.addEventListener('activate', (event) => {
    // Optional: Explicitly delete old caches to be 100% sure
    event.waitUntil(
        caches.keys().then((keyList) => {
            return Promise.all(keyList.map((key) => caches.delete(key)));
        })
    );
    self.clients.claim(); // Take control of the page immediately
});
