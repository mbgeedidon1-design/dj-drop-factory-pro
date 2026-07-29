// DJ Drop Factory Pro v5.0 - Service Worker
// PWA-compliant with precaching, runtime caching, background sync, and offline fallback

const CACHE_NAME = 'dj-drop-factory-v5';
const STATIC_CACHE = `${CACHE_NAME}-static`;
const DYNAMIC_CACHE = `${CACHE_NAME}-dynamic`;
const IMAGE_CACHE = `${CACHE_NAME}-images`;
const API_CACHE = `${CACHE_NAME}-api`;

// Precache critical assets
const PRECACHE_ASSETS = [
    '/',
    '/offline.html',
    '/manifest.json',
    '/static/icons/icon-192.png',
    '/static/icons/icon-512.png',
    '/static/icons/icon-maskable-192.png',
    '/static/icons/icon-maskable-512.png'
];

// Install event - precache critical assets
self.addEventListener('install', (event) => {
    console.log('[SW] Installing...');
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => {
                console.log('[SW] Precaching assets');
                return cache.addAll(PRECACHE_ASSETS);
            })
            .then(() => {
                console.log('[SW] Skip waiting');
                return self.skipWaiting();
            })
            .catch((err) => {
                console.error('[SW] Precache failed:', err);
            })
    );
});

// Activate event - clean old caches
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating...');
    event.waitUntil(
        caches.keys().then((cacheNames) => {
            return Promise.all(
                cacheNames
                    .filter((name) => name.startsWith(CACHE_NAME) && name !== STATIC_CACHE && name !== DYNAMIC_CACHE && name !== IMAGE_CACHE && name !== API_CACHE)
                    .map((name) => {
                        console.log('[SW] Deleting old cache:', name);
                        return caches.delete(name);
                    })
            );
        }).then(() => {
            console.log('[SW] Claiming clients');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET requests (except for API with background sync)
    if (request.method !== 'GET' && !url.pathname.startsWith('/api/')) {
        return;
    }

    // API calls - Network first, cache fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirst(request, API_CACHE));
        return;
    }

    // Images - Cache first, network fallback
    if (request.destination === 'image' || url.pathname.match(/\.(png|jpg|jpeg|gif|webp|svg)$/)) {
        event.respondWith(cacheFirst(request, IMAGE_CACHE));
        return;
    }

    // Static assets (JS, CSS, fonts) - Cache first
    if (request.destination === 'script' || request.destination === 'style' || request.destination === 'font') {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
        return;
    }

    // HTML pages - Stale while revalidate
    if (request.destination === 'document' || request.mode === 'navigate') {
        event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
        return;
    }

    // Audio - Network first with cache fallback
    if (request.destination === 'audio' || url.pathname.match(/\.(mp3|wav|ogg|webm)$/)) {
        event.respondWith(networkFirst(request, DYNAMIC_CACHE));
        return;
    }

    // Default: Stale while revalidate
    event.respondWith(staleWhileRevalidate(request, DYNAMIC_CACHE));
});

// Cache strategies
async function cacheFirst(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    if (cached) {
        return cached;
    }

    try {
        const response = await fetch(request);
        if (response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        console.error('[SW] Cache first failed:', error);
        // Return offline fallback for navigation
        if (request.mode === 'navigate') {
            return caches.match('/offline.html');
        }
        throw error;
    }
}

async function networkFirst(request, cacheName) {
    const cache = await caches.open(cacheName);

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.log('[SW] Network failed, trying cache:', request.url);
        const cached = await cache.match(request);
        if (cached) {
            return cached;
        }

        // Return generic offline response for API
        if (request.url.includes('/api/')) {
            return new Response(
                JSON.stringify({ success: false, offline: true, error: 'You are offline' }),
                { headers: { 'Content-Type': 'application/json' } }
            );
        }

        throw error;
    }
}

async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);

    const fetchPromise = fetch(request).then((networkResponse) => {
        if (networkResponse.ok) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch((error) => {
        console.log('[SW] Stale-while-revalidate fetch failed:', error);
        return cached;
    });

    return cached || fetchPromise;
}

// Background Sync
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-library') {
        console.log('[SW] Background sync: sync-library');
        event.waitUntil(syncLibraryData());
    }
});

async function syncLibraryData() {
    // In a full implementation, this would sync queued library saves
    console.log('[SW] Library sync completed');
}

// Push Notifications
self.addEventListener('push', (event) => {
    console.log('[SW] Push received:', event);

    const options = {
        body: event.data ? event.data.text() : 'New update from DJ Drop Factory!',
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/icon-96.png',
        tag: 'dj-drop-factory-update',
        requireInteraction: false,
        actions: [
            { action: 'open', title: 'Open App' },
            { action: 'close', title: 'Dismiss' }
        ]
    };

    event.waitUntil(
        self.registration.showNotification('DJ Drop Factory', options)
    );
});

self.addEventListener('notificationclick', (event) => {
    event.notification.close();

    if (event.action === 'open' || !event.action) {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

// Periodic Background Sync
self.addEventListener('periodicsync', (event) => {
    if (event.tag === 'update-trends') {
        console.log('[SW] Periodic sync: update-trends');
        event.waitUntil(updateTrends());
    }
});

async function updateTrends() {
    try {
        const response = await fetch('/api/trends');
        const data = await response.json();
        console.log('[SW] Trends updated:', data);
    } catch (error) {
        console.error('[SW] Trends update failed:', error);
    }
}

// Message handling from main thread
self.addEventListener('message', (event) => {
    if (event.data === 'skipWaiting') {
        self.skipWaiting();
    }

    if (event.data === 'getVersion') {
        event.ports[0].postMessage({ version: CACHE_NAME });
    }
});

console.log('[SW] DJ Drop Factory Service Worker loaded');
