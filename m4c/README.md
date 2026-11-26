# Muscles4Chicks

Kerman, Buğra ve Arda'nın salon defteri. Cloudflare Workers (ücretsiz plan) üzerinde; hesap gerekmez, davet linkiyle açılır.

- Yayında: https://muscles4chicks.7yd6fhz5ws.workers.dev (davet anahtarıyla: `/?k=<GROUP_KEY>`)
- `src/worker.js` — API (kayıt ekle/sil, özel hareket, tek seferlik taşıma) ve Durable Object (her kaldırış ayrı anahtar)
- `public/index.html` — arayüz (80'ler Miami teması), 4 sn'de bir yeni kayıtları çeker
- `scripts/embed.mjs` — `public/` dosyalarını Worker koduna gömer (build adımı)

```bash
npm install
npx wrangler deploy
openssl rand -hex 8 | npx wrangler secret put GROUP_KEY   # davet anahtarı
# yerel: echo GROUP_KEY=test-anahtar > .dev.vars && npx wrangler dev --port 8788 && npm test
```
