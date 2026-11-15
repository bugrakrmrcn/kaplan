// Uçtan uca API testi: `wrangler dev` çalışırken koşar (BASE, KEY ortam değişkenleri).
// Sahte bir push servisi kurar ve her oyuncuya giden bildirimi o oyuncunun anahtarıyla çözer.
import assert from "node:assert/strict";
import crypto from "node:crypto";
import http from "node:http";

const BASE = process.env.BASE || "http://127.0.0.1:8787";
const KEY = process.env.KEY || "test-anahtar";
const b64u = (b) => Buffer.from(b).toString("base64url");
const hmac = (k, d) => crypto.createHmac("sha256", k).update(d).digest();
const hkdf = (salt, ikm, info, len) => hmac(hmac(salt, ikm), Buffer.concat([info, Buffer.from([1])])).subarray(0, len);

const devices = {};   // ad -> { ecdh, auth }
const inbox = {};     // ad -> [bildirim]
const server = http.createServer((req, res) => {
  const name = decodeURIComponent(req.url.split("/").pop());
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    const d = devices[name];
    if (d.gone) return res.writeHead(410).end();
    const body = Buffer.concat(chunks);
    const salt = body.subarray(0, 16), idlen = body[20], asPub = body.subarray(21, 21 + idlen), ct = body.subarray(21 + idlen);
    const ikm = hkdf(d.auth, d.ecdh.computeSecret(asPub), Buffer.concat([Buffer.from("WebPush: info\0"), d.ecdh.getPublicKey(), asPub]), 32);
    const dec = crypto.createDecipheriv("aes-128-gcm", hkdf(salt, ikm, Buffer.from("Content-Encoding: aes128gcm\0"), 16), hkdf(salt, ikm, Buffer.from("Content-Encoding: nonce\0"), 12));
    dec.setAuthTag(ct.subarray(ct.length - 16));
    const plain = Buffer.concat([dec.update(ct.subarray(0, ct.length - 16)), dec.final()]);
    (inbox[name] ||= []).push(JSON.parse(plain.subarray(0, -1).toString()).notification);
    res.writeHead(201).end();
  });
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const port = server.address().port;

const api = async (path, body) => {
  const res = await fetch(BASE + "/api/" + path, { method: body ? "POST" : "GET", headers: { "x-key": KEY, "content-type": "application/json" }, body: body && JSON.stringify(body) });
  return { status: res.status, ...(await res.json()) };
};
const settle = () => new Promise((r) => setTimeout(r, 500));
const take = (name) => { const x = inbox[name] || []; inbox[name] = []; return x; };

const st0 = await api("state");
const players = st0.players;
assert.deepEqual(players, ["Sarsi", "Kerman", "Buğra", "Yigü", "Arda"]);
// önceki test çağrılarını temizle
for (const c of st0.active) await api("cancel", { id: c.id, name: c.by });

for (const name of players) {
  const ecdh = crypto.createECDH("prime256v1"); ecdh.generateKeys();
  devices[name] = { ecdh, auth: crypto.randomBytes(16) };
  const r = await api("subscribe", { name, subscription: { endpoint: `http://127.0.0.1:${port}/push/${encodeURIComponent(name)}`, keys: { p256dh: b64u(ecdh.getPublicKey()), auth: b64u(devices[name].auth) } } });
  assert.equal(r.ok, true);
}
await settle(); for (const n of players) take(n);
assert.ok(Object.values((await api("state")).notif).every(Boolean), "herkes bildirime abone görünmeli");

// 0) kimlik: abonelik adresinden isim bulunur; bilinmeyen adres null döner
assert.equal((await api("whoami", { endpoint: `http://127.0.0.1:${port}/push/${encodeURIComponent("Yigü")}` })).name, "Yigü");
assert.equal((await api("whoami", { endpoint: "http://127.0.0.1:1/yok" })).name, null);

// 1) Buğra çağrı gönderir -> diğer 4 kişiye bildirim, Buğra'ya gitmez
const when = Date.now() + 3 * 3600 * 1000;
const { id } = await api("call", { name: "Buğra", when, place: "Çınar Kıraathanesi", note: "çay benden", car: true, seats: 3 });
await settle();
assert.equal(take("Buğra").length, 0, "çağıran kendine bildirim almamalı");
for (const n of ["Sarsi", "Kerman", "Yigü", "Arda"]) {
  const [m] = take(n);
  assert.ok(m, n + " bildirim almalı");
  assert.equal(m.title, "Buğra 101 çağırıyor 🀄");
  assert.match(m.body, /Bugün|Yarın/); assert.match(m.body, /Çınar Kıraathanesi/); assert.match(m.body, /çay benden/);
  assert.match(m.navigate, /^http/);
}

// 2) Kerman "varım, arabam yok" -> yalnızca Buğra'ya bildirim
await api("respond", { id, name: "Kerman", status: "in", car: false });
await settle();
let m = take("Buğra");
assert.equal(m.length, 1); assert.equal(m[0].title, "Kerman geliyor ✅"); assert.match(m[0].body, /arabası yok/); assert.match(m[0].body, /2\/4/);
for (const n of ["Sarsi", "Kerman", "Yigü", "Arda"]) assert.equal(take(n).length, 0);

// 3) Arda "şu saatte olur" (belki, +1 saat) ; Yigü gelemiyor
await api("respond", { id, name: "Arda", status: "maybe", time: when + 3600 * 1000, car: true, seats: 2, note: "işten çıkınca" });
await api("respond", { id, name: "Yigü", status: "out" });
await settle();
m = take("Buğra");
assert.deepEqual(m.map((x) => x.title).sort(), ["Arda belki 🤔", "Yigü gelemiyor ❌"]);
assert.match(m.find((x) => x.title.startsWith("Arda")).body, /en erken \d\d:\d\d/);

// 4) araç eşleştirme: Buğra, Kerman'ı alır -> Kerman'a bildirim
let r = await api("pickup", { id, name: "Buğra", passenger: "Kerman" });
assert.equal(r.picked, true); await settle();
assert.equal(take("Kerman")[0].title, "Buğra seni alacak 🚗");
r = await api("pickup", { id, name: "Kerman", passenger: "Buğra" });
assert.equal(r.status, 400, "arabası olmayan kimseyi alamaz");

// 5) dürtme: yalnızca cevap vermeyen Sarsi'ye gider; 5 dk içinde tekrar edilemez
r = await api("nudge", { id, name: "Kerman" });
assert.deepEqual(r.nudged, ["Sarsi"]); await settle();
assert.equal(take("Sarsi")[0].title, "Kerman seni dürttü 👉");
assert.equal((await api("nudge", { id, name: "Kerman" })).status, 429);

// 6) Sarsi ve Arda "varım" -> 4 kişi: "Masa kuruldu" gelmeyen Yigü hariç herkese (cevabı veren hariç)
await api("respond", { id, name: "Sarsi", status: "in", car: false });
await settle(); take("Buğra");
await api("respond", { id, name: "Arda", status: "in", car: true, seats: 2 });
await settle();
for (const n of ["Buğra", "Kerman", "Sarsi"]) {
  const got = take(n);
  assert.equal(got.length, 1, n + " tek bildirim almalı"); assert.equal(got[0].title, "Masa kuruldu! ✅"); assert.match(got[0].body, /2 araç/);
}
assert.equal(take("Yigü").length, 0, "gelmeyen kişi 'masa kuruldu' almamalı");
assert.equal(take("Arda").length, 0);

// 7) durum
let st = await api("state");
let call = st.active.find((c) => c.id === id);
assert.equal(Object.values(call.responses).filter((x) => x.status === "in").length, 4);
assert.deepEqual(call.pickups, { Kerman: "Buğra" });
assert.deepEqual(st.places, ["Çınar Kıraathanesi"]);

// 8) Buğra arabasız olursa Kerman'ı alma kaydı düşer
await api("respond", { id, name: "Buğra", status: "in", car: false });
call = (await api("state")).active.find((c) => c.id === id);
assert.deepEqual(call.pickups, {});

// 9) yetki: başkası iptal edemez / güncelleyemez; saat değişimi bildirilir
assert.equal((await api("cancel", { id, name: "Kerman" })).status, 403);
assert.equal((await api("update", { id, name: "Kerman", when }).then((x) => x.status)), 403);
await settle(); for (const n of players) take(n);
await api("update", { id, name: "Buğra", when: when + 1800 * 1000, place: "Çınar Kıraathanesi", note: "" });
await settle();
assert.equal(take("Kerman")[0].title, "Buğra saati değiştirdi 🕘");
assert.equal(take("Yigü").length, 0);

// 10) ölü abonelik (410) temizlenir
devices["Sarsi"].gone = true;
await api("test", { name: "Sarsi" }); await settle();
assert.equal((await api("state")).notif.Sarsi, false, "410 dönen abonelik silinmeli");

// 11) iptal -> çağrı aktif listeden çıkar, bildirim gider
await api("cancel", { id, name: "Buğra" }); await settle();
assert.equal(take("Kerman")[0].title, "Buğra 101'i iptal etti");
st = await api("state");
assert.equal(st.active.length, 0); assert.ok(st.past.some((c) => c.id === id && c.cancelled), "iptal edilen çağrı geçmişte görünmeli");

// 12) hatalı girdiler
assert.equal((await api("call", { name: "Yabancı", when })).status, 400);
assert.equal((await api("call", { name: "Arda", when: "yarın" })).status, 400);
assert.equal((await api("respond", { id: "yok", name: "Arda", status: "in" })).status, 404);
const bad = await fetch(BASE + "/api/state", { headers: { "x-key": "yanlış" } }).catch(() => fetch(BASE + "/api/state", { headers: { "x-key": "yanlis" } }));
assert.equal(bad.status, 401);

server.close();
console.log("✓ api: çağrı, cevap, bildirim hedefleri, araç eşleştirme, dürtme, masa kuruldu, yetki, iptal doğrulandı");
