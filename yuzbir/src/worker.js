// 101 Çağrı — Cloudflare Worker + Durable Object
// Site (public/) + API (/api/*) + Web Push bildirimleri tek Worker'da.

import { DurableObject } from "cloudflare:workers";
import { FILES } from "./assets.gen.js";
import { generateVapid, sendPush } from "./push.js";

const TZ = "Europe/Istanbul";
const TABLE = 4;                       // 101 dört kişiyle oynanır
const EXPIRE_MS = 6 * 3600 * 1000;     // çağrı, saatinden 6 saat sonra arşive düşer
const MAX_PAST = 10;

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const bad = (msg, status = 400) => json({ error: msg }, status);

function playersOf(env) {
  return String(env.PLAYERS || "").split(",").map((s) => s.trim()).filter(Boolean);
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/manifest.webmanifest") {
      // Davet anahtarı ana ekran uygulamasına taşınsın diye start_url'e eklenir.
      const k = url.searchParams.get("k") || "";
      return new Response(JSON.stringify({
        name: "101 Çağrı",
        short_name: "101",
        description: "101 için arkadaş çağırma ve müsaitlik",
        start_url: k ? `/?k=${encodeURIComponent(k)}` : "/",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        background_color: "#0f1512",
        theme_color: "#0f1512",
        lang: "tr",
        icons: [
          { src: "/icon-192.png", sizes: "192x192", type: "image/png", purpose: "any" },
          { src: "/icon-512.png", sizes: "512x512", type: "image/png", purpose: "any" },
        ],
      }), { headers: { "content-type": "application/manifest+json; charset=utf-8" } });
    }

    if (url.pathname.startsWith("/api/")) {
      if (!env.GROUP_KEY) return bad("Sunucuda GROUP_KEY ayarlanmamış.", 500);
      if (request.headers.get("x-key") !== env.GROUP_KEY) return bad("Davet anahtarı geçersiz.", 401);
      const stub = env.GROUP.get(env.GROUP.idFromName("main"));
      return stub.fetch(request);
    }

    // statik dosyalar (koda gömülü)
    const path = url.pathname === "/" ? "/index.html" : url.pathname;
    const file = FILES[path];
    if (!file || (request.method !== "GET" && request.method !== "HEAD")) return new Response("Bulunamadı", { status: 404 });
    const bytes = Uint8Array.from(atob(file.b64), (c) => c.charCodeAt(0));
    return new Response(request.method === "HEAD" ? null : bytes, {
      headers: {
        "content-type": file.type,
        // sayfa ve service worker her zaman güncel gelsin; ikonlar önbelleğe alınabilir
        "cache-control": file.type === "image/png" ? "public, max-age=86400" : "no-cache",
      },
    });
  },
};

// ---------------------------------------------------------------- yardımcılar
function dayKey(ms) {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit" }).format(new Date(ms));
}

function fmtTime(ms) {
  return new Intl.DateTimeFormat("tr-TR", { timeZone: TZ, hour: "2-digit", minute: "2-digit", hour12: false }).format(new Date(ms));
}

export function fmtWhen(ms, now = Date.now()) {
  const diff = Math.round((Date.parse(dayKey(ms)) - Date.parse(dayKey(now))) / 86400000);
  let day;
  if (diff === 0) day = "Bugün";
  else if (diff === 1) day = "Yarın";
  else if (diff > 1 && diff < 7) day = new Intl.DateTimeFormat("tr-TR", { timeZone: TZ, weekday: "long" }).format(new Date(ms));
  else day = new Intl.DateTimeFormat("tr-TR", { timeZone: TZ, day: "numeric", month: "long" }).format(new Date(ms));
  return `${day} ${fmtTime(ms)}`;
}

const clip = (s, n) => String(s ?? "").trim().slice(0, n);
const comingOf = (call) => Object.entries(call.responses).filter(([, r]) => r.status === "in").map(([n]) => n);

// ---------------------------------------------------------------- Durable Object
export class Group extends DurableObject {
  async fetch(request) {
    const url = new URL(request.url);
    this.origin = url.origin;
    const players = playersOf(this.env);
    const route = url.pathname.replace("/api/", "");
    const body = request.method === "POST" ? await request.json().catch(() => ({})) : {};
    const who = body.name;
    if (request.method === "POST" && route !== "unsubscribe" && !players.includes(who)) return bad("Bilinmeyen oyuncu.");

    switch (`${request.method} ${route}`) {
      case "GET state": return this.state(players);
      case "POST subscribe": return this.subscribe(who, body.subscription);
      case "POST unsubscribe": return this.unsubscribe(body.endpoint);
      case "POST call": return this.createCall(players, who, body);
      case "POST respond": return this.respond(players, who, body);
      case "POST update": return this.updateCall(players, who, body);
      case "POST cancel": return this.cancel(players, who, body);
      case "POST nudge": return this.nudge(players, who, body);
      case "POST pickup": return this.pickup(players, who, body);
      case "POST test": return this.testPush(who);
      default: return bad("Bulunamadı.", 404);
    }
  }

  // ---- depolama
  async calls() { return (await this.ctx.storage.get("calls")) || []; }
  async saveCalls(calls) {
    const now = Date.now();
    const active = calls.filter((c) => !c.cancelled && c.when + EXPIRE_MS > now);
    const past = calls.filter((c) => c.cancelled || c.when + EXPIRE_MS <= now).sort((a, b) => b.when - a.when).slice(0, MAX_PAST);
    await this.ctx.storage.put("calls", [...active, ...past]);
  }
  async subs() { return (await this.ctx.storage.get("subs")) || {}; }
  async vapid() {
    let v = await this.ctx.storage.get("vapid");
    if (!v) {
      v = await generateVapid();
      await this.ctx.storage.put("vapid", v);
    }
    return v;
  }

  // ---- bildirim
  async notify(names, title, text, tag) {
    const subs = await this.subs();
    const vapid = await this.vapid();
    const payload = { web_push: 8030, notification: { title, body: text, navigate: `${this.origin}/`, tag, lang: "tr" } };
    const jobs = [];
    for (const name of new Set(names)) {
      for (const sub of subs[name] || []) {
        jobs.push(sendPush(sub, payload, vapid, this.origin, { topic: tag }).then((r) => ({ name, sub, r })));
      }
    }
    const results = await Promise.all(jobs);
    const dead = results.filter((x) => x.r.gone);
    if (dead.length) {
      const cur = await this.subs();
      for (const d of dead) cur[d.name] = (cur[d.name] || []).filter((s) => s.endpoint !== d.sub.endpoint);
      await this.ctx.storage.put("subs", cur);
    }
    return { sent: results.filter((x) => x.r.ok).length, failed: results.filter((x) => !x.r.ok).length };
  }
  later(promise) { this.ctx.waitUntil(promise.catch((e) => console.log("bildirim hatası", e))); }

  // ---- uç noktalar
  async state(players) {
    const now = Date.now();
    const calls = await this.calls();
    const subs = await this.subs();
    const vapid = await this.vapid();
    return json({
      players,
      now,
      table: TABLE,
      vapidKey: vapid.publicKey,
      notif: Object.fromEntries(players.map((p) => [p, (subs[p] || []).length > 0])),
      active: calls.filter((c) => !c.cancelled && c.when + EXPIRE_MS > now).sort((a, b) => a.when - b.when),
      past: calls.filter((c) => c.cancelled || c.when + EXPIRE_MS <= now).sort((a, b) => b.when - a.when).slice(0, 5),
      places: [...new Set(calls.map((c) => c.place).filter(Boolean))].slice(0, 8),
    });
  }

  async subscribe(who, subscription) {
    if (!subscription?.endpoint || !subscription?.keys?.p256dh || !subscription?.keys?.auth) return bad("Abonelik eksik.");
    const okUrl = /^https:\/\//.test(subscription.endpoint) || (this.env.ALLOW_HTTP_PUSH === "1" && /^http:\/\/127\.0\.0\.1[:/]/.test(subscription.endpoint));
    if (!okUrl) return bad("Abonelik adresi geçersiz.");
    const subs = await this.subs();
    // aynı cihaz başka isimle kayıtlıysa taşı
    for (const n of Object.keys(subs)) subs[n] = subs[n].filter((s) => s.endpoint !== subscription.endpoint);
    subs[who] = [...(subs[who] || []), { endpoint: subscription.endpoint, keys: subscription.keys }].slice(-4);
    await this.ctx.storage.put("subs", subs);
    return json({ ok: true });
  }

  async unsubscribe(endpoint) {
    const subs = await this.subs();
    for (const n of Object.keys(subs)) subs[n] = subs[n].filter((s) => s.endpoint !== endpoint);
    await this.ctx.storage.put("subs", subs);
    return json({ ok: true });
  }

  async testPush(who) {
    const r = await this.notify([who], "101 Çağrı 🀄", "Bildirimler çalışıyor!", "test");
    return json(r);
  }

  async createCall(players, who, b) {
    const when = Number(b.when);
    if (!Number.isFinite(when) || when < Date.now() - 3600 * 1000) return bad("Geçerli bir gün ve saat seç.");
    const call = {
      id: crypto.randomUUID().slice(0, 8),
      by: who,
      when,
      place: clip(b.place, 60),
      note: clip(b.note, 140),
      createdAt: Date.now(),
      responses: { [who]: { status: "in", time: null, car: !!b.car, seats: b.car ? Math.max(0, Math.min(6, Number(b.seats ?? 3))) : 0, note: "", at: Date.now() } },
      pickups: {},      // yolcu -> sürücü
      tableAnnounced: false,
      lastNudge: 0,
    };
    const calls = await this.calls();
    calls.push(call);
    await this.saveCalls(calls);
    const text = [fmtWhen(when), call.place, call.note].filter(Boolean).join(" · ");
    this.later(this.notify(players.filter((p) => p !== who), `${who} 101 çağırıyor 🀄`, `${text}\nGeliyor musun? Dokun ve cevapla.`, `call-${call.id}`));
    return json({ ok: true, id: call.id });
  }

  async respond(players, who, b) {
    const calls = await this.calls();
    const call = calls.find((c) => c.id === b.id && !c.cancelled);
    if (!call) return bad("Çağrı bulunamadı.", 404);
    if (!["in", "maybe", "out"].includes(b.status)) return bad("Geçersiz cevap.");
    const prev = call.responses[who];
    const time = b.time == null ? null : Number(b.time);
    const car = b.status !== "out" && !!b.car;
    call.responses[who] = {
      status: b.status,
      time: Number.isFinite(time) ? time : null,
      car,
      seats: car ? Math.max(0, Math.min(6, Number(b.seats ?? 3))) : 0,
      note: clip(b.note, 100),
      at: Date.now(),
    };
    // gelmeyen ya da arabası olmayan artık kimseyi alamaz / alınmaz
    if (b.status === "out") delete call.pickups[who];
    if (!car) for (const [p, d] of Object.entries(call.pickups)) if (d === who) delete call.pickups[p];
    if (car) delete call.pickups[who];

    const coming = comingOf(call);
    const justFull = coming.length >= TABLE && !call.tableAnnounced;
    if (justFull) call.tableAnnounced = true;
    if (coming.length < TABLE) call.tableAnnounced = false;
    await this.saveCalls(calls);

    const r = call.responses[who];
    const changed = !prev || prev.status !== r.status || prev.time !== r.time || prev.car !== r.car;
    if (justFull) {
      const cars = coming.filter((n) => call.responses[n].car).length;
      this.later(this.notify(players.filter((p) => p !== who && call.responses[p]?.status !== "out"),
        "Masa kuruldu! ✅", `${fmtWhen(call.when)}${call.place ? " · " + call.place : ""}\n${coming.join(", ")} · ${cars} araç`, `call-${call.id}`));
    } else if (changed && who !== call.by) {
      const label = { in: "geliyor ✅", maybe: "belki 🤔", out: "gelemiyor ❌" }[r.status];
      const extra = [r.time ? `en erken ${fmtTime(r.time)}` : "", r.status !== "out" ? (r.car ? "arabası var 🚗" : "arabası yok") : "", r.note].filter(Boolean).join(" · ");
      this.later(this.notify([call.by], `${who} ${label}`, `${extra ? extra + "\n" : ""}${coming.length}/${TABLE} kişi tamam`, `call-${call.id}`));
    }
    return json({ ok: true });
  }

  async updateCall(players, who, b) {
    const calls = await this.calls();
    const call = calls.find((c) => c.id === b.id && !c.cancelled);
    if (!call) return bad("Çağrı bulunamadı.", 404);
    if (call.by !== who) return bad("Çağrıyı yalnızca gönderen değiştirebilir.", 403);
    const when = Number(b.when);
    if (!Number.isFinite(when)) return bad("Geçerli bir gün ve saat seç.");
    const timeChanged = when !== call.when;
    call.when = when;
    call.place = clip(b.place, 60);
    call.note = clip(b.note, 140);
    await this.saveCalls(calls);
    this.later(this.notify(players.filter((p) => p !== who && call.responses[p]?.status !== "out"),
      timeChanged ? `${who} saati değiştirdi 🕘` : `${who} çağrıyı güncelledi`,
      [fmtWhen(call.when), call.place, call.note].filter(Boolean).join(" · "), `call-${call.id}`));
    return json({ ok: true });
  }

  async cancel(players, who, b) {
    const calls = await this.calls();
    const call = calls.find((c) => c.id === b.id && !c.cancelled);
    if (!call) return bad("Çağrı bulunamadı.", 404);
    if (call.by !== who) return bad("Çağrıyı yalnızca gönderen iptal edebilir.", 403);
    call.cancelled = true;
    await this.saveCalls(calls);
    this.later(this.notify(players.filter((p) => p !== who && call.responses[p]?.status !== "out"),
      `${who} 101'i iptal etti`, fmtWhen(call.when) + (call.place ? " · " + call.place : ""), `call-${call.id}`));
    return json({ ok: true });
  }

  async nudge(players, who, b) {
    const calls = await this.calls();
    const call = calls.find((c) => c.id === b.id && !c.cancelled);
    if (!call) return bad("Çağrı bulunamadı.", 404);
    const waiting = players.filter((p) => !call.responses[p]);
    if (!waiting.length) return json({ ok: true, nudged: [] });
    const wait = call.lastNudge + 5 * 60 * 1000 - Date.now();
    if (wait > 0) return bad(`Az önce dürtüldü. ${Math.ceil(wait / 60000)} dk sonra tekrar dene.`, 429);
    call.lastNudge = Date.now();
    await this.saveCalls(calls);
    this.later(this.notify(waiting, `${who} seni dürttü 👉`, `101: ${fmtWhen(call.when)}${call.place ? " · " + call.place : ""}\nHâlâ cevap vermedin!`, `nudge-${call.id}`));
    return json({ ok: true, nudged: waiting });
  }

  async pickup(players, who, b) {
    const calls = await this.calls();
    const call = calls.find((c) => c.id === b.id && !c.cancelled);
    if (!call) return bad("Çağrı bulunamadı.", 404);
    const passenger = b.passenger;
    if (!players.includes(passenger) || passenger === who) return bad("Geçersiz yolcu.");
    const me = call.responses[who];
    if (!me || me.status === "out" || !me.car) return bad("Birini almak için arabayla geliyor olmalısın.");
    const pr = call.responses[passenger];
    if (!pr || pr.status === "out" || pr.car) return bad("Bu kişinin araca ihtiyacı yok.");
    if (call.pickups[passenger] === who) {
      delete call.pickups[passenger];
      await this.saveCalls(calls);
      this.later(this.notify([passenger], `${who} seni alamayacak`, "Başka bir araç ayarlamak gerek.", `ride-${call.id}`));
      return json({ ok: true, picked: false });
    }
    const load = Object.values(call.pickups).filter((d) => d === who).length;
    if (!call.pickups[passenger] && load >= (me.seats || 3)) return bad("Arabanda yer kalmadı.");
    call.pickups[passenger] = who;
    await this.saveCalls(calls);
    this.later(this.notify([passenger], `${who} seni alacak 🚗`, `101: ${fmtWhen(call.when)}${call.place ? " · " + call.place : ""}`, `ride-${call.id}`));
    return json({ ok: true, picked: true });
  }
}
