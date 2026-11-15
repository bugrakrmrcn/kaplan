// Web Push (RFC 8291 aes128gcm + RFC 8292 VAPID) — yalnızca Web Crypto, bağımlılık yok.

const te = new TextEncoder();

export const b64u = {
  enc(buf) {
    const b = buf instanceof Uint8Array ? buf : new Uint8Array(buf);
    let s = "";
    for (const x of b) s += String.fromCharCode(x);
    return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
  },
  dec(str) {
    const s = atob(str.replace(/-/g, "+").replace(/_/g, "/"));
    const out = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) out[i] = s.charCodeAt(i);
    return out;
  },
};

function concat(...arrs) {
  const out = new Uint8Array(arrs.reduce((n, a) => n + a.length, 0));
  let o = 0;
  for (const a of arrs) {
    out.set(a, o);
    o += a.length;
  }
  return out;
}

async function hkdf(salt, ikm, info, len) {
  const key = await crypto.subtle.importKey("raw", ikm, "HKDF", false, ["deriveBits"]);
  return new Uint8Array(await crypto.subtle.deriveBits({ name: "HKDF", hash: "SHA-256", salt, info }, key, len * 8));
}

/** Sunucunun VAPID anahtar çiftini üretir (bir kez; saklanır). */
export async function generateVapid() {
  const kp = await crypto.subtle.generateKey({ name: "ECDSA", namedCurve: "P-256" }, true, ["sign", "verify"]);
  const pub = new Uint8Array(await crypto.subtle.exportKey("raw", kp.publicKey));
  const privateJwk = await crypto.subtle.exportKey("jwk", kp.privateKey);
  return { publicKey: b64u.enc(pub), privateJwk };
}

async function vapidAuth(endpoint, vapid, subject) {
  const head = b64u.enc(te.encode(JSON.stringify({ typ: "JWT", alg: "ES256" })));
  const body = b64u.enc(te.encode(JSON.stringify({
    aud: new URL(endpoint).origin,
    exp: Math.floor(Date.now() / 1000) + 12 * 3600,
    sub: subject,
  })));
  const key = await crypto.subtle.importKey("jwk", vapid.privateJwk, { name: "ECDSA", namedCurve: "P-256" }, false, ["sign"]);
  const sig = await crypto.subtle.sign({ name: "ECDSA", hash: "SHA-256" }, key, te.encode(`${head}.${body}`));
  return `vapid t=${head}.${body}.${b64u.enc(sig)}, k=${vapid.publicKey}`;
}

/** Mesajı abonenin anahtarlarıyla şifreler (aes128gcm). */
export async function encryptPayload(subscription, plaintext) {
  const uaPub = b64u.dec(subscription.keys.p256dh);
  const auth = b64u.dec(subscription.keys.auth);
  const eph = await crypto.subtle.generateKey({ name: "ECDH", namedCurve: "P-256" }, true, ["deriveBits"]);
  const asPub = new Uint8Array(await crypto.subtle.exportKey("raw", eph.publicKey));
  const uaKey = await crypto.subtle.importKey("raw", uaPub, { name: "ECDH", namedCurve: "P-256" }, false, []);
  const secret = new Uint8Array(await crypto.subtle.deriveBits({ name: "ECDH", public: uaKey }, eph.privateKey, 256));

  const ikm = await hkdf(auth, secret, concat(te.encode("WebPush: info\0"), uaPub, asPub), 32);
  const salt = crypto.getRandomValues(new Uint8Array(16));
  const cek = await hkdf(salt, ikm, te.encode("Content-Encoding: aes128gcm\0"), 16);
  const nonce = await hkdf(salt, ikm, te.encode("Content-Encoding: nonce\0"), 12);

  const key = await crypto.subtle.importKey("raw", cek, "AES-GCM", false, ["encrypt"]);
  const padded = concat(plaintext, new Uint8Array([2])); // son kayıt işareti
  const cipher = new Uint8Array(await crypto.subtle.encrypt({ name: "AES-GCM", iv: nonce }, key, padded));

  const rs = new Uint8Array([0, 0, 16, 0]); // kayıt boyutu 4096
  return concat(salt, rs, new Uint8Array([asPub.length]), asPub, cipher);
}

/**
 * Bir aboneliğe bildirim gönderir.
 * @returns {{ok:boolean,status:number,gone:boolean}} gone=true ise abonelik silinmeli
 */
export async function sendPush(subscription, payload, vapid, subject, { ttl = 6 * 3600, topic } = {}) {
  const body = await encryptPayload(subscription, te.encode(JSON.stringify(payload)));
  const headers = {
    Authorization: await vapidAuth(subscription.endpoint, vapid, subject),
    "Content-Encoding": "aes128gcm",
    "Content-Type": "application/octet-stream",
    TTL: String(ttl),
    Urgency: "high",
  };
  if (topic) headers.Topic = topic;
  try {
    const res = await fetch(subscription.endpoint, { method: "POST", headers, body });
    return { ok: res.ok, status: res.status, gone: res.status === 404 || res.status === 410 };
  } catch (e) {
    return { ok: false, status: 0, gone: false, error: String(e) };
  }
}
