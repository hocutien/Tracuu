/* Tra cứu thửa đất — bộ nhớ đệm để mở được khi không có mạng.
   Đổi số PHIEN mỗi lần thay index.html thì máy sẽ tự lấy bản mới. */
const PHIEN = 'tcdt-v1';
const SHELL = ['./', './index.html', './manifest.webmanifest',
               './icon-192.png', './icon-512.png', './icon-maskable-512.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(PHIEN).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(caches.keys()
    .then(ks => Promise.all(ks.filter(k => k !== PHIEN).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  /* Ảnh vệ tinh: luôn lấy từ mạng, không lưu đệm (ô ảnh rất nhiều, dễ đầy bộ nhớ) */
  if (/arcgisonline|maptiles\.arcgis|^mt\d\.google\.com$|api\.mapbox\.com|^tile\./.test(url.hostname)
      || /googleapis\.com\/.*tile/.test(url.hostname + url.pathname)) return;

  /* Gọi API đọc ảnh bằng AI: luôn đi thẳng ra mạng */
  if (url.hostname === 'generativelanguage.googleapis.com') return;

  /* Trang chính: ưu tiên bản mới, rớt mạng thì dùng bản đã lưu */
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then(r => {
        const sao = r.clone();
        caches.open(PHIEN).then(c => c.put('./index.html', sao));
        return r;
      }).catch(() => caches.match('./index.html').then(r => r || caches.match('./')))
    );
    return;
  }

  /* Thư viện đọc chữ từ CDN: lưu lại để lần sau đọc được khi ngoại tuyến */
  if (url.hostname === 'cdn.jsdelivr.net' || url.hostname === 'unpkg.com') {
    e.respondWith(
      caches.match(req).then(c => c || fetch(req).then(r => {
        if (r.ok) { const sao = r.clone(); caches.open(PHIEN).then(k => k.put(req, sao)); }
        return r;
      }))
    );
    return;
  }

  /* Tệp của chính công cụ */
  if (url.origin === location.origin) {
    e.respondWith(
      caches.match(req).then(c => c || fetch(req).then(r => {
        if (r.ok) { const sao = r.clone(); caches.open(PHIEN).then(k => k.put(req, sao)); }
        return r;
      }).catch(() => c))
    );
  }
});
