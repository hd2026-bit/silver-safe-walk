// 走這條，一路順！離線支援：有網路時一律拿最新版（網路優先），沒網路時用上次存下的版本
const CACHE = 'zouzhetiao-v1.15';
// 只有首頁（走這條，一路順！）的導覽請求存成 ./index.html；/zheli/（這里需要你）等其他頁面照原網址存，避免互相覆蓋
const isHome = (req) => req.mode === 'navigate' && ['/', '/index.html'].includes(new URL(req.url).pathname);
const FILES = ['./', './index.html', './manifest.webmanifest', './icon-180.png', './icon-192.png', './icon-512.png', './icon-maskable-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(FILES)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET' || new URL(req.url).origin !== location.origin) return;
  e.respondWith(
    fetch(req)
      .then((res) => {
        if (res.ok) {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(isHome(req) ? './index.html' : req, copy));
        }
        return res;
      })
      .catch(() => caches.match(isHome(req) ? './index.html' : req).then((r) => r || (isHome(req) ? caches.match('./') : Response.error())))
  );
});
