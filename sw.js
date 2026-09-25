/* Service worker of the installed web app: lets آزمون‌یار open and run without a connection.
 *
 * - App files (page, scripts, styles, question data, icons): network first, so an online visit always gets the
 *   current version; the cached copy is used offline or when the network is slow. They are cached on install by
 *   following the page's own references, so no file list has to be kept up to date here.
 * - Question pictures: cached copy first, refreshed in the background. A picture is cached only once it has been
 *   shown; nothing is downloaded ahead of time. Offline, a picture that was never shown gets a small placeholder.
 * - Web font (Google Fonts): cached on first use.
 *
 * Bump VERSION only when this file's logic changes; app updates need no change here.
 */
const VERSION = "2026-09-25.2";
const APP_CACHE = `ayeen-app-${VERSION}`;
const IMAGE_CACHE = "ayeen-images-v1";
const FONT_CACHE = "ayeen-fonts-v1";
const CACHES = [APP_CACHE, IMAGE_CACHE, FONT_CACHE];
const NETWORK_TIMEOUT_MS = 4000;
const IMAGE_PATH = "/assets/questions/";
const FONT_HOSTS = ["fonts.googleapis.com", "fonts.gstatic.com"];

const scope = new URL(self.registration.scope);

// Relative references to other app files: HTML attributes, static and dynamic imports, manifest icons.
const REFERENCE_PATTERNS = [
  /\b(?:href|src)="(\.{1,2}\/[^"#]+)"/g,
  /\bfrom\s*"(\.{1,2}\/[^"]+)"/g,
  /\bimport\(\s*"(\.{1,2}\/[^"]+)"\s*\)/g,
  /"src"\s*:\s*"(\.{1,2}\/[^"]+)"/g,
];
const PARSED_FILE = /(\/|\.html|\.js|\.json)$/;

self.addEventListener("install", (event) => {
  event.waitUntil(precacheApp().then(() => self.skipWaiting()));
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const names = await caches.keys();
    await Promise.all(names.filter((name) => name.startsWith("ayeen-") && !CACHES.includes(name)).map((name) => caches.delete(name)));
    await self.clients.claim();
  })());
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET" || (request.cache === "only-if-cached" && request.mode !== "same-origin")) return;
  const url = new URL(request.url);
  if (url.origin === scope.origin) {
    if (url.pathname.includes(IMAGE_PATH)) event.respondWith(picture(event));
    else if (url.pathname.startsWith(scope.pathname)) event.respondWith(networkFirst(request, url));
  } else if (FONT_HOSTS.includes(url.hostname)) {
    event.respondWith(cacheFirst(request, FONT_CACHE));
  }
});

/** Caches the page and every app file it loads, found by following references from the start page. */
async function precacheApp() {
  const cache = await caches.open(APP_CACHE);
  const queue = [scope.href];
  const seen = new Set();
  while (queue.length) {
    const url = queue.shift();
    if (seen.has(url)) continue;
    seen.add(url);
    try {
      const response = await fetch(url, { cache: "no-cache" });
      if (!response.ok) continue;
      await cache.put(url, response.clone());
      if (PARSED_FILE.test(new URL(url).pathname)) queue.push(...references(await response.text(), url));
    } catch {
      // Unreachable now: the file is cached the first time the app uses it instead.
    }
  }
}

function references(text, base) {
  const found = [];
  for (const pattern of REFERENCE_PATTERNS) {
    for (const match of text.matchAll(pattern)) {
      const url = new URL(match[1], base);
      if (url.origin === scope.origin && url.pathname.startsWith(scope.pathname) && !url.pathname.includes(IMAGE_PATH)) found.push(url.href);
    }
  }
  return found;
}

/** Network first with a timeout; falls back to the cached copy (the start page for any navigation). */
async function networkFirst(request, url) {
  const cache = await caches.open(APP_CACHE);
  const isPage = request.mode === "navigate";
  // Only the start page is stored for navigations, so opening another file directly never replaces it.
  const isStartPage = isPage && (url.pathname === scope.pathname || url.pathname === `${scope.pathname}index.html`);
  // Revalidate with the server even when the HTTP cache still counts the file as fresh (GitHub Pages allows
  // 10 minutes), so the page and its modules always come from the same deploy. A navigation request cannot be
  // copied with new options, so it is re-created from its URL.
  const fresh = isPage ? new Request(request.url, { cache: "no-cache", credentials: "same-origin" }) : new Request(request, { cache: "no-cache" });
  const network = fetch(fresh).then((response) => {
    if (response.ok && response.type === "basic" && (!isPage || isStartPage)) cache.put(isStartPage ? scope.href : request, response.clone());
    return response;
  });
  try {
    return await withTimeout(network, NETWORK_TIMEOUT_MS);
  } catch {
    const cached = isPage
      ? await cache.match(scope.href)
      : (await cache.match(request)) ?? (await cache.match(request, { ignoreSearch: true }));
    return cached ?? network; // nothing cached yet: keep waiting for the network (or fail with it)
  }
}

/** Cached picture first, refreshed in the background; a placeholder when offline and never cached. */
async function picture(event) {
  const cache = await caches.open(IMAGE_CACHE);
  const cached = await cache.match(event.request);
  const network = fetch(event.request).then((response) => {
    if (response.ok) cache.put(event.request, response.clone());
    return response;
  });
  if (cached) {
    event.waitUntil(network.catch(() => undefined));
    return cached;
  }
  try {
    return await network;
  } catch {
    return offlinePicture();
  }
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  if (response.ok || response.type === "opaque") cache.put(request, response.clone());
  return response;
}

function withTimeout(promise, milliseconds) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error("timeout")), milliseconds);
    promise.then((value) => { clearTimeout(timer); resolve(value); }, (error) => { clearTimeout(timer); reject(error); });
  });
}

function offlinePicture() {
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="360" height="150" viewBox="0 0 360 150">
  <rect width="360" height="150" rx="14" fill="#f2f4f8"/>
  <text x="180" y="72" text-anchor="middle" direction="rtl" font-family="Vazirmatn, Tahoma, sans-serif" font-size="15" fill="#6c768b">تصویر این سؤال هنوز ذخیره نشده است.</text>
  <text x="180" y="98" text-anchor="middle" direction="rtl" font-family="Vazirmatn, Tahoma, sans-serif" font-size="13" fill="#8a93a6">با اتصال به اینترنت نمایش داده می‌شود.</text>
</svg>`;
  return new Response(svg, { headers: { "Content-Type": "image/svg+xml; charset=utf-8", "Cache-Control": "no-store" } });
}
