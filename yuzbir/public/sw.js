// 101 Çağrı — service worker: bildirimleri gösterir, dokununca uygulamayı açar.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (e) => e.waitUntil(self.clients.claim()));

self.addEventListener("push", (event) => {
  let n = { title: "101 Çağrı", body: "Yeni bir gelişme var." };
  try {
    const data = event.data.json();
    n = data.notification || data;
  } catch (_) { /* metin değilse varsayılanı göster */ }
  event.waitUntil((async () => {
    await self.registration.showNotification(n.title, {
      body: n.body,
      tag: n.tag,
      renotify: !!n.tag,
      icon: "/icon-192.png",
      badge: "/icon-192.png",
      lang: "tr",
      data: { url: n.navigate || "/" },
    });
    for (const c of await self.clients.matchAll({ type: "window" })) c.postMessage({ type: "refresh" });
  })());
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = event.notification.data?.url || "/";
  event.waitUntil((async () => {
    const wins = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const w of wins) {
      if ("focus" in w) {
        w.postMessage({ type: "refresh" });
        return w.focus();
      }
    }
    return self.clients.openWindow(url);
  })());
});
