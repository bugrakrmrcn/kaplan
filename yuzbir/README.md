# 101 Çağrı

Beş kişilik arkadaş grubu için 101 organizasyon uygulaması: biri çağrı gönderir, herkesin
telefonuna bildirim düşer; herkes tek dokunuşla "varım / şu saatte olur / yokum" der ve
arabası olup olmadığını bildirir.

- **Ücretsiz:** Cloudflare Workers ücretsiz planı (site + API + veri + bildirim tek Worker).
- **Ek uygulama yok:** iPhone'da Safari → Paylaş → *Ana Ekrana Ekle*; bildirimler normal
  uygulama bildirimi gibi gelir (iOS 16.4+).
- **Oyuncular:** `wrangler.jsonc` içindeki `PLAYERS` (Sarsi, Kerman, Buğra, Yigü, Arda).

## Özellikler

- Çağrı: gün, saat, mekân, not, "arabam var" + kaç kişi alabilirim
- Cevap: Varım / Şu saatte olur (en erken saat) / Yokum, araç bilgisi, not
- Masa: 4 koltuk dolunca "Masa kuruldu" — herkese bildirim
- Araç: arabası olmayanlar listelenir; arabası olan "Ben alırım" der, yolcuya bildirim gider
- Dürt: cevap vermeyenlere hatırlatma (5 dakikada bir)
- Düzenle / İptal (yalnızca çağıran), saat değişince bildirim
- WhatsApp'a tek dokunuşla özet + link gönderme (yedek kanal)
- Ana ekran simgesinde cevaplanmamış çağrı sayısı

## Bildirim kuralları

| Olay | Kime gider |
|---|---|
| Yeni çağrı | Çağıran hariç herkes |
| Biri cevap verdi | Yalnızca çağıran |
| 4. kişi geldi (masa kuruldu) | Gelmeyenler hariç herkes |
| Saat/mekân değişti, iptal | Gelmeyenler hariç herkes |
| Dürtme | Yalnızca cevap vermeyenler |
| "Ben alırım" | Yalnızca yolcu |

## Yayına alma

```bash
npm install
npx wrangler login                      # ya da CLOUDFLARE_API_TOKEN
npx wrangler deploy
openssl rand -hex 12 | npx wrangler secret put GROUP_KEY   # davet anahtarı
```

Davet linki: `https://yuzbir.<hesap>.workers.dev/?k=<GROUP_KEY>` — bu linki gruba at.
Anahtarı bilen herkes çağrıları görür; link gruptan dışarı çıkarsa anahtarı değiştir.

## Geliştirme ve test

```bash
echo "GROUP_KEY=test-anahtar" > .dev.vars && echo "ALLOW_HTTP_PUSH=1" >> .dev.vars
npx wrangler dev --port 8787
npm test                                # bildirim şifrelemesi + VAPID (bağımsız çözücüyle)
node test/api.test.mjs                  # uçtan uca API (sahte push servisiyle), dev sunucusu açıkken
```

## Dosyalar

- `src/worker.js` — API ve Durable Object (çağrılar, cevaplar, araç eşleştirme, bildirim kuralları)
- `src/push.js` — Web Push (RFC 8291 şifreleme + RFC 8292 VAPID), bağımlılıksız
- `public/index.html` — arayüz; `public/sw.js` — bildirimleri gösteren service worker
