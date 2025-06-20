// Basic service worker for PWA capabilities
self.addEventListener('install', function(event) {
	console.log('Service Worker installing...');
	event.waitUntil(
		caches.open('ai-chip-trading-v1').then(function(cache) {
			return cache.addAll([
				'/',
				'/manifest.json',
				// Add other static assets as needed
			]);
		})
	);
});

self.addEventListener('fetch', function(event) {
	// Basic caching strategy for network-first approach
	event.respondWith(
		fetch(event.request)
			.then(function(response) {
				// If the request is successful, cache it
				if (response.status === 200) {
					const responseClone = response.clone();
					caches.open('ai-chip-trading-v1').then(function(cache) {
						cache.put(event.request, responseClone);
					});
				}
				return response;
			})
			.catch(function() {
				// If network fails, try to get from cache
				return caches.match(event.request);
			})
	);
});

self.addEventListener('activate', function(event) {
	console.log('Service Worker activating...');
	event.waitUntil(
		caches.keys().then(function(cacheNames) {
			return Promise.all(
				cacheNames.map(function(cacheName) {
					if (cacheName !== 'ai-chip-trading-v1') {
						return caches.delete(cacheName);
					}
				})
			);
		})
	);
});
