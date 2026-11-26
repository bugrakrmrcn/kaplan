// Uçtan uca API testi: `wrangler dev` açıkken (BASE, KEY ortam değişkenleri).
import assert from "node:assert/strict";
const BASE = process.env.BASE || "http://127.0.0.1:8788", KEY = process.env.KEY || "test-anahtar";
const api = async (p, body, key = KEY) => {
  const r = await fetch(BASE + "/api/" + p, { method: body ? "POST" : "GET", headers: { "x-key": key, "content-type": "application/json" }, body: body && JSON.stringify(body) });
  return { status: r.status, ...(await r.json()) };
};
assert.equal((await api("state", null, "yanlis")).status, 401, "yanlış anahtar reddedilmeli");
const s0 = await api("state");
for (const l of s0.lifts) await api("delete", { id: l.id });
const a = await api("lift", { who: "Kerman", ex: "Bench Press", kg: 80, reps: 5, sets: 3 });
assert.equal(a.ok, true); assert.equal(a.lift.kg, 80);
await new Promise((r) => setTimeout(r, 5));
const b = await api("lift", { who: "Arda", ex: "Squat", kg: "102.5", reps: 4, sets: 2 });
assert.equal(b.lift.kg, 102.5);
for (const [bad, why] of [[{ who: "Yabancı", ex: "Squat", kg: 50, reps: 5 }, "kişi"], [{ who: "Arda", ex: "", kg: 50, reps: 5 }, "hareket"],
  [{ who: "Arda", ex: "Squat", kg: 0, reps: 5 }, "kg"], [{ who: "Arda", ex: "Squat", kg: 5000, reps: 5 }, "kg üst"], [{ who: "Arda", ex: "Squat", kg: 50, reps: 0 }, "tekrar"]])
  assert.equal((await api("lift", bad)).status, 400, "geçersiz " + why);
// set set (piramit): kg/reps en ağır setten, set sayısı listeden
await new Promise((r) => setTimeout(r, 5));
const p = await api("lift", { who: "Buğra", ex: "Bench Press", detail: [{ kg: 15, reps: 12 }, { kg: "17.5", reps: 10 }, { kg: 20, reps: 8 }, { kg: 20, reps: 9 }] });
assert.equal(p.ok, true); assert.equal(p.lift.kg, 20); assert.equal(p.lift.reps, 9); assert.equal(p.lift.sets, 4);
assert.deepEqual(p.lift.detail[1], { kg: 17.5, reps: 10 });
for (const d of [[], [{ kg: 0, reps: 5 }], [{ kg: 20, reps: 0 }], Array(21).fill({ kg: 10, reps: 5 })])
  assert.equal((await api("lift", { who: "Buğra", ex: "Squat", detail: d })).status, 400, "geçersiz detay");
await api("delete", { id: p.lift.id });
let st = await api("state");
assert.deepEqual(st.lifts.map((l) => l.who), ["Arda", "Kerman"], "yeniden eskiye sıralı");
assert.equal((await api("state?rev=" + st.rev)).same, true, "değişmediyse boş cevap");
// taşıma: eski zamanıyla eklenir, aynı id ikinci kez eklenmez
const old = { id: "6ditun11segtr8tmkgku", who: "Buğra", ex: "Triceps Pushdown", kg: 45, reps: 7, sets: 3, at: 1795659819434 };
assert.equal((await api("import", { lifts: [old] })).imported, 1);
assert.equal((await api("import", { lifts: [old] })).imported, 0);
st = await api("state");
assert.equal(st.lifts.at(-1).id, old.id, "eski kayıt en sonda (en eski)");
// hareket ekleme (büyük/küçük harf tekrarını almaz)
assert.deepEqual((await api("exercise", { name: "Cable Fly" })).customEx, ["Cable Fly"]);
assert.deepEqual((await api("exercise", { name: "cable fly" })).customEx, ["Cable Fly"]);
// silme
await api("delete", { id: a.lift.id });
st = await api("state");
assert.ok(!st.lifts.some((l) => l.id === a.lift.id));
assert.equal(st.lifts.length, 2);
console.log("✓ api: anahtar, set set giriş, doğrulama, sıralama, rev, taşıma, hareket ekleme, silme");
