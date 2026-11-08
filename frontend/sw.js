/* Public app shell only. Never cache /api responses or user/case data offline. */
const CACHE_NAME = 'bolkeresolve-shell-v47';
const SHELL_URLS = [
  '/', '/index.html', '/styles.css', '/design-v2.css', '/app.js', '/share-token.js',
  '/privacy.html', '/manifest.webmanifest', '/live-room.css', '/product-foundation.css', '/blueprint-upgrade.css', '/experience-refresh.css', '/homepage-polish.css', '/live-pcm-processor.js',
  '/assets/bolke-guide-avatar.webp', '/assets/bolke-guide.webp',
  '/assets/guide-fallback.png', '/assets/hero-fallback.jpg',
  '/assets/man-fallback.jpg', '/assets/payment-detail-fallback.jpg',
  '/assets/payment-facts-fallback.svg', '/assets/woman-phone-fallback.jpg', '/assets/bolkeresolve-icon-192.png',
  '/assets/bolkeresolve-icon-512.png'
];
self.addEventListener('install', (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(SHELL_URLS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', (event) => {
  event.waitUntil(caches.keys().then((keys) => Promise.all(keys.filter((key) => key.startsWith('bolkeresolve-shell-') && key !== CACHE_NAME).map((key) => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener('fetch', (event) => {
  const request = event.request;
  if (request.method !== 'GET') return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;
  // Case, auth, evidence, voice and provider endpoints are deliberately network-only.
  if (url.pathname.startsWith('/api/')) return;
  if (!SHELL_URLS.includes(url.pathname)) return;
  if (request.mode === 'navigate') {
    event.respondWith(fetch(request).then((response) => {
      if (response.ok) caches.open(CACHE_NAME).then((cache) => cache.put('/index.html', response.clone()));
      return response;
    }).catch(async () => (await caches.match('/index.html')) || Response.error()));
    return;
  }
  // Stale-while-revalidate for the public shell only. The URL allowlist above
  // deliberately excludes every /api/ route, so private case data is never cached.
  const updatePromise = fetch(request).then(async (response) => {
    if (response.ok) {
      const cache = await caches.open(CACHE_NAME);
      await cache.put(request, response.clone());
    }
    return response;
  });
  event.waitUntil(updatePromise.then(() => undefined).catch(() => undefined));
  event.respondWith(caches.match(request).then((cached) => cached || updatePromise));
});
