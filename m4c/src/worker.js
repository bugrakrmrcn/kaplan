// Muscles4Chicks — Cloudflare Worker + Durable Object
// Sayfa (public/, koda gömülü) + API (/api/*). Kayıtlar tek bir Durable Object'te, her kaldırış ayrı anahtarda.

import { DurableObject } from "cloudflare:workers";
import { FILES } from "./assets.gen.js";

const json = (data, status = 200) =>
  new Response(JSON.stringify(data), { status, headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store" } });
const bad = (msg, status = 400) => json({ error: msg }, status);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);

    if (url.pathname === "/manifest.webmanifest") {
      // Davet anahtarı ana ekran simgesine taşınsın diye start_url'e eklenir.
      const k = url.searchParams.get("k") || "";
      return new Response(JSON.stringify({
        name: "Muscles4Chicks", short_name: "M4C", description: "Kerman, Buğra ve Arda'nın salon defteri",
        start_url: k ? `/?k=${encodeURIComponent(k)}` : "/", scope: "/", display: "standalone", orientation: "portrait",
        background_color: "#07061a", theme_color: "#07061a", lang: "tr",
        icons: [{ src: "/icon-192.png", sizes: "192x192", type: "image/png" }, { src: "/icon-512.png", sizes: "512x512", type: "image/png" }],
      }), { headers: { "content-type": "application/manifest+json; charset=utf-8" } });
    }

    if (url.pathname.startsWith("/api/")) {
      if (!env.GROUP_KEY) return bad("Sunucuda GROUP_KEY ayarlanmamış.", 500);
      if (request.headers.get("x-key") !== env.GROUP_KEY) return bad("Davet linki geçersiz.", 401);
      return env.GYM.get(env.GYM.idFromName("main")).fetch(request);
    }

    const path = url.pathname === "/" ? "/index.html" : url.pathname;
    const file = FILES[path];
    if (!file || (request.method !== "GET" && request.method !== "HEAD")) return new Response("Bulunamadı", { status: 404 });
    const bytes = Uint8Array.from(atob(file.b64), (c) => c.charCodeAt(0));
    return new Response(request.method === "HEAD" ? null : bytes, {
      headers: { "content-type": file.type, "cache-control": file.type === "image/png" ? "public, max-age=86400" : "no-cache" },
    });
  },
};

const clip = (s, n) => String(s ?? "").trim().replace(/\s+/g, " ").slice(0, n);
const MAX_LIST = 1000;

export class Gym extends DurableObject {
  async fetch(request) {
    const url = new URL(request.url);
    const route = url.pathname.replace("/api/", "");
    const players = String(this.env.PLAYERS || "").split(",").map((s) => s.trim()).filter(Boolean);
    const body = request.method === "POST" ? await request.json().catch(() => ({})) : {};
    switch (`${request.method} ${route}`) {
      case "GET state": return this.state(url.searchParams.get("rev"));
      case "POST lift": return this.addLift(players, body);
      case "POST delete": return this.del(body.id);
      case "POST exercise": return this.addExercise(body.name);
      case "POST import": return this.importLifts(players, body.lifts);
      default: return bad("Bulunamadı.", 404);
    }
  }

  async rev() { return (await this.ctx.storage.get("rev")) || 0; }
  async bump() { const r = (await this.rev()) + 1; await this.ctx.storage.put("rev", r); return r; }
  key(l) { return `lift:${String(l.at).padStart(15, "0")}:${l.id}`; }

  async state(clientRev) {
    const rev = await this.rev();
    if (clientRev != null && Number(clientRev) === rev) return json({ rev, same: true });
    const map = await this.ctx.storage.list({ prefix: "lift:", reverse: true, limit: MAX_LIST });
    const customEx = (await this.ctx.storage.get("customEx")) || [];
    return json({ rev, lifts: [...map.values()], customEx });
  }

  validate(players, b) {
    const kg = Math.round(Number(b.kg) * 100) / 100, reps = Math.round(Number(b.reps)), sets = Math.round(Number(b.sets ?? 1));
    if (!players.includes(b.who)) return "Bilinmeyen kişi.";
    if (!clip(b.ex, 40)) return "Hareket seç.";
    if (!(kg > 0 && kg <= 1000)) return "Ağırlık 0 ile 1000 kg arasında olmalı.";
    if (!(reps >= 1 && reps <= 100)) return "Tekrar 1 ile 100 arasında olmalı.";
    if (!(sets >= 1 && sets <= 50)) return "Set 1 ile 50 arasında olmalı.";
    return { who: b.who, ex: clip(b.ex, 40), kg, reps, sets };
  }

  async addLift(players, b) {
    const v = this.validate(players, b);
    if (typeof v === "string") return bad(v);
    const lift = { id: crypto.randomUUID().slice(0, 12), ...v, at: Date.now() };
    await this.ctx.storage.put(this.key(lift), lift);
    const rev = await this.bump();
    return json({ ok: true, lift, rev });
  }

  async del(id) {
    if (typeof id !== "string" || !/^[\w-]{1,40}$/.test(id)) return bad("Geçersiz kayıt.");
    const map = await this.ctx.storage.list({ prefix: "lift:" });
    for (const [k, l] of map) if (l.id === id) { await this.ctx.storage.delete(k); return json({ ok: true, rev: await this.bump() }); }
    return json({ ok: true, rev: await this.rev() });
  }

  async addExercise(name) {
    name = clip(name, 40);
    if (!name) return bad("Hareket adı boş olamaz.");
    const list = (await this.ctx.storage.get("customEx")) || [];
    if (!list.some((x) => x.toLocaleLowerCase("tr-TR") === name.toLocaleLowerCase("tr-TR"))) {
      if (list.length >= 60) return bad("En fazla 60 özel hareket eklenebilir.");
      list.push(name);
      await this.ctx.storage.put("customEx", list);
    }
    return json({ ok: true, customEx: list, rev: await this.bump() });
  }

  /** Tek seferlik taşıma: eski kayıtları zamanlarıyla birlikte ekler (aynı id ikinci kez eklenmez). */
  async importLifts(players, lifts) {
    if (!Array.isArray(lifts) || lifts.length > 2000) return bad("Geçersiz liste.");
    const existing = new Set([...(await this.ctx.storage.list({ prefix: "lift:" })).values()].map((l) => l.id));
    let n = 0;
    for (const b of lifts) {
      const v = this.validate(players, b);
      const id = clip(b.id, 40);
      if (typeof v === "string" || !/^[\w-]{1,40}$/.test(id) || existing.has(id)) continue;
      const at = Number(b.at);
      if (!(at > 1.5e12 && at < 4e12)) continue;
      const lift = { id, ...v, at };
      await this.ctx.storage.put(this.key(lift), lift);
      existing.add(id);
      n++;
    }
    return json({ ok: true, imported: n, rev: await this.bump() });
  }
}
