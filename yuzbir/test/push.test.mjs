// push.js'in ürettiği isteği bağımsız bir RFC 8291/8292 uygulamasıyla (node:crypto) doğrular.
import assert from "node:assert/strict";
import crypto from "node:crypto";
import http from "node:http";
import { b64u, generateVapid, sendPush } from "../src/push.js";

const hmac = (key, data) => crypto.createHmac("sha256", key).update(data).digest();
const hkdf = (salt, ikm, info, len) => hmac(hmac(salt, ikm), Buffer.concat([info, Buffer.from([1])])).subarray(0, len);

// abone (tarayıcı) tarafı anahtarları
const ua = crypto.createECDH("prime256v1");
ua.generateKeys();
const auth = crypto.randomBytes(16);

let received;
const server = http.createServer((req, res) => {
  const chunks = [];
  req.on("data", (c) => chunks.push(c));
  req.on("end", () => {
    received = { headers: req.headers, body: Buffer.concat(chunks) };
    res.writeHead(201).end();
  });
});
await new Promise((r) => server.listen(0, "127.0.0.1", r));
const endpoint = `http://127.0.0.1:${server.address().port}/push/abc`;

const vapid = await generateVapid();
const payload = { web_push: 8030, notification: { title: "Buğra 101 çağırıyor 🀄", body: "Bugün 21:00 · Çınar Kıraathanesi", navigate: "https://ornek.dev/" } };
const sub = { endpoint, keys: { p256dh: b64u.enc(ua.getPublicKey()), auth: b64u.enc(auth) } };
const result = await sendPush(sub, payload, vapid, "https://ornek.dev", { topic: "call-1" });
server.close();
assert.equal(result.ok, true, "gönderim başarılı olmalı");

// --- başlıklar
assert.equal(received.headers["content-encoding"], "aes128gcm");
assert.equal(received.headers.ttl, "21600");
assert.equal(received.headers.urgency, "high");
assert.equal(received.headers.topic, "call-1");

// --- VAPID JWT (ES256) doğrulaması
const m = /^vapid t=([^,]+), k=(.+)$/.exec(received.headers.authorization);
assert.ok(m, "Authorization vapid biçiminde olmalı");
const [h, p, s] = m[1].split(".");
assert.equal(m[2], vapid.publicKey);
const pubKey = crypto.createPublicKey({ key: { kty: "EC", crv: "P-256", x: vapid.privateJwk.x, y: vapid.privateJwk.y }, format: "jwk" });
assert.ok(crypto.verify("sha256", Buffer.from(`${h}.${p}`), { key: pubKey, dsaEncoding: "ieee-p1363" }, Buffer.from(b64u.dec(s))), "JWT imzası geçerli olmalı");
const claims = JSON.parse(Buffer.from(b64u.dec(p)).toString());
assert.equal(claims.aud, new URL(endpoint).origin);
assert.equal(claims.sub, "https://ornek.dev");
assert.ok(claims.exp > Date.now() / 1000 && claims.exp <= Date.now() / 1000 + 24 * 3600, "exp 24 saati geçmemeli");
assert.deepEqual(JSON.parse(Buffer.from(b64u.dec(h)).toString()), { typ: "JWT", alg: "ES256" });

// --- gövdeyi abonenin gizli anahtarıyla çöz (RFC 8291)
const body = received.body;
const salt = body.subarray(0, 16);
const rs = body.readUInt32BE(16);
const idlen = body[20];
const asPub = body.subarray(21, 21 + idlen);
const cipher = body.subarray(21 + idlen);
assert.equal(rs, 4096);
assert.equal(idlen, 65);
const secret = ua.computeSecret(asPub);
const ikm = hkdf(auth, secret, Buffer.concat([Buffer.from("WebPush: info\0"), ua.getPublicKey(), asPub]), 32);
const cek = hkdf(salt, ikm, Buffer.from("Content-Encoding: aes128gcm\0"), 16);
const nonce = hkdf(salt, ikm, Buffer.from("Content-Encoding: nonce\0"), 12);
const dec = crypto.createDecipheriv("aes-128-gcm", cek, nonce);
dec.setAuthTag(cipher.subarray(cipher.length - 16));
const plain = Buffer.concat([dec.update(cipher.subarray(0, cipher.length - 16)), dec.final()]);
assert.equal(plain[plain.length - 1], 2, "son bayt kayıt sonu işareti (0x02) olmalı");
assert.deepEqual(JSON.parse(plain.subarray(0, -1).toString("utf8")), payload);

// --- silinmiş abonelik (410) "gone" olarak işaretlenmeli
const gone = http.createServer((_, res) => res.writeHead(410).end());
await new Promise((r) => gone.listen(0, "127.0.0.1", r));
const r2 = await sendPush({ ...sub, endpoint: `http://127.0.0.1:${gone.address().port}/x` }, payload, vapid, "https://ornek.dev");
gone.close();
assert.equal(r2.gone, true);

console.log("✓ push: şifreleme, VAPID imzası, başlıklar ve 410 işleme doğrulandı");
