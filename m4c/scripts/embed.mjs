// public/ içindeki dosyaları Worker koduna gömer (src/assets.gen.js). wrangler build adımında çalışır.
import { readdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, extname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const TYPES = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".png": "image/png", ".webmanifest": "application/manifest+json; charset=utf-8" };
const out = {};
for (const name of readdirSync(join(root, "public")).sort()) {
  const type = TYPES[extname(name)];
  if (!type) continue;
  out["/" + name] = { type, b64: readFileSync(join(root, "public", name)).toString("base64") };
}
writeFileSync(join(root, "src", "assets.gen.js"), "// OTOMATİK ÜRETİLİR (scripts/embed.mjs) — elle düzenleme.\nexport const FILES = " + JSON.stringify(out) + ";\n");
console.log("gömülen dosyalar:", Object.keys(out).join(", "));
