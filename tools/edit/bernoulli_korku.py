"""Bernoulli diferansiyel denklemi — korku temalı edit (sadece korku müziği, yanıp sönen ışıklar).

Kullanım: python3 tools/edit/bernoulli_korku.py [--preview 3 12 ...]
Çıktı:    output/bernoulli_korku.mp4 (1080x1920, 30 fps)
"""
import argparse
import math
import os
import random
import subprocess
import sys

import numpy as np
import skia

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
from gfx import C, clamp, ease, fill, glow, lerp, rrect, stroke, vgrad  # noqa: E402

W, H, FPS = 1080, 1920, 30
SR = 44100
FD = os.path.join(ROOT, "assets", "fonts")
F_CREEP = skia.Typeface.MakeFromFile(os.path.join(FD, "Creepster.ttf"))
F_TYPE = skia.Typeface.MakeFromFile(os.path.join(FD, "SpecialElite.ttf"))
F_CHALK = skia.Typeface.MakeFromFile(os.path.join(FD, "Caveat.ttf"))
F_MATH = skia.Typeface.MakeFromFile("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf")

# ============================================================== içerik (zaman çizelgesi)
STEPS = [
    # (başlangıç, bitiş, başlık, [satırlar...])  satır: (metin, boyut)  ^{} üs, _{} alt indis
    (5.0, 11.0, "GENEL FORM", [("y′ + P(x)·y = Q(x)·y^{n}", 88), ("(n ≠ 0 ve n ≠ 1)", 58)]),
    (11.0, 17.0, "1. ADIM: her iki tarafı y^n'ye böl", [("y^{−n}·y′ + P(x)·y^{1−n} = Q(x)", 72)]),
    (17.0, 23.0, "2. ADIM: dönüşüm", [("v = y^{1−n}", 92), ("v′ = (1−n)·y^{−n}·y′", 76)]),
    (23.0, 29.0, "3. ADIM: lineer denkleme dönüşür", [("v′ + (1−n)·P(x)·v = (1−n)·Q(x)", 64)]),
    (29.0, 35.0, "4. ADIM: integral çarpanı", [("μ(x) = e^{∫(1−n)P(x)dx}", 84), ("(μ·v)′ = (1−n)·μ·Q(x)", 70)]),
    (35.0, 45.0, "ÖRNEK: y' + y = x·y^3", [("n = 3  →  v = y^{−2}", 72), ("v′ − 2v = −2x", 76),
                                         ("v = x + ½ + C·e^{2x}", 76), ("y = 1 / √(x + ½ + C·e^{2x})", 70)]),
]
TOTAL = 53.0
SCARES = [5.0, 11.0, 17.0, 23.0, 29.0, 35.0, 45.2, 50.6]   # stinger anları
BLACKOUTS = [(10.55, 10.95), (22.4, 22.9), (34.3, 34.95), (44.9, 46.2), (49.6, 50.6)]


# ============================================================== ışık
def flicker(t):
    """Ampul parlaklığı 0..1: titreme, ani sönmeler, karartmalar."""
    for a, b in BLACKOUTS:
        if a <= t < b:
            return 0.0 if (int(t * 40) % 7) else 0.35
    k = int(t * 20)
    r = random.Random(k * 7919).random()
    r2 = random.Random(k * 104729 + 3).random()
    base = 0.85 + 0.15 * math.sin(t * 37) * math.sin(t * 11.3)
    if r < 0.06:
        return 0.05
    if r < 0.12:
        return 0.35 + 0.3 * r2
    # stinger öncesi ve sonrasında daha fazla titreme
    near = min(abs(t - s) for s in SCARES)
    if near < 0.5 and r2 < 0.5:
        return 0.15 + 0.6 * r2
    return base


# ============================================================== metin yardımcıları
def parse(s):
    """'a^{b}c_{d}' -> [(metin, seviye)] seviye: 0 normal, 1 üs, -1 alt."""
    out, i, cur = [], 0, ""
    while i < len(s):
        if s[i] in "^_" and i + 1 < len(s) and s[i + 1] == "{":
            if cur:
                out.append((cur, 0))
                cur = ""
            j = s.index("}", i)
            out.append((s[i + 2:j], 1 if s[i] == "^" else -1))
            i = j + 1
        else:
            cur += s[i]
            i += 1
    if cur:
        out.append((cur, 0))
    return out


def glyph_font(ch, size):
    f = skia.Font(F_CHALK, size)
    if f.textToGlyphs(ch)[0] == 0 or ch in "−∫√≠μ·½′→":
        return skia.Font(F_MATH, size * 0.86)
    return f


def rich_runs(s, size):
    runs, x = [], 0.0
    for txt, lvl in parse(s):
        sz = size * (0.6 if lvl else 1.0)
        dy = -size * 0.42 if lvl == 1 else (size * 0.18 if lvl == -1 else 0)
        for ch in txt:
            f = glyph_font(ch, sz)
            w = f.measureText(ch)
            if ch == "′":   # türev işareti y'nin üstüne binmesin
                runs.append((ch, f, x + sz * 0.10, dy - sz * 0.05))
                x += w + sz * 0.12
                continue
            runs.append((ch, f, x, dy))
            x += w
    return runs, x


def draw_chalk(cv, s, cx, y, size, reveal, light, t, seed=0):
    """Tebeşir yazısı: soldan sağa yazılma (reveal 0..1), ışık sönünce kırmızı parlama."""
    if reveal <= 0:
        return
    runs, width = rich_runs(s, size)
    x0 = cx - width / 2
    limit = width * reveal
    rnd = random.Random(seed)
    red = 1 - light
    for ch, f, x, dy in runs:
        if x > limit:
            break
        jx = rnd.uniform(-1.2, 1.2)
        px, py = x0 + x + jx, y + dy
        if red > 0.2:   # karanlıkta kanlı parlama
            cv.drawString(ch, px, py, f, fill(C("#ff1a1a", int(200 * red)), blur=10))
        col = C("#f2efe6", int(70 + 185 * light)) if red < 0.8 else C("#ff3b3b", 230)
        cv.drawString(ch, px, py, f, fill(col))
        for k in range(2):   # tebeşir dokusu
            cv.drawString(ch, px + rnd.uniform(-2, 2), py + rnd.uniform(-2, 2), f,
                          fill(C("#ffffff", int(40 * light))))
    # tebeşir ucu
    if 0 < reveal < 1:
        cv.drawCircle(x0 + limit, y - size * 0.3, 6, fill(C("#ffffff", 200), blur=3))


def text_c(cv, s, x, y, size, color, tf, outline=0, ocol=0xFF000000):
    f = skia.Font(tf, size)
    w = f.measureText(s)
    if outline:
        cv.drawString(s, x - w / 2, y, f, stroke(ocol, outline))
    cv.drawString(s, x - w / 2, y, f, fill(color))
    return w


def creep_title(cv, s, x, y, size, color, t, drip=True):
    """Creepster'da 'İ' yok: I çizip üstüne nokta koy. Kan damlaları ekle."""
    f = skia.Font(F_CREEP, size)
    plain = s.replace("İ", "I")
    w = f.measureText(plain)
    cx = x - w / 2
    cv.drawString(plain, cx + 6, y + 8, f, fill(C("#000000", 200), blur=6))
    cv.drawString(plain, cx, y, f, fill(color))
    run = 0.0
    rnd = random.Random(len(s))
    for ch in s:
        cw = f.measureText("I" if ch == "İ" else ch)
        if ch == "İ":
            cv.drawCircle(cx + run + cw / 2, y - size * 0.86, size * 0.07, fill(color))
        if drip and ch.strip() and rnd.random() < 0.45:   # kan damlası
            L = (t * rnd.uniform(15, 40) + rnd.uniform(0, 40)) % (size * 1.4)
            dx = cx + run + cw * rnd.uniform(0.3, 0.7)
            cv.drawLine(dx, y - 4, dx, y + L, stroke(color, size * 0.06))
            cv.drawCircle(dx, y + L, size * 0.055, fill(color))
        run += cw
    return w


# ============================================================== sahne
NOISE = []
_rng = np.random.default_rng(11)
for _ in range(6):
    n = (_rng.random((H // 2, W // 2)) * 255).astype(np.uint8)
    rgba = np.dstack([n, n, n, np.full_like(n, 255)])
    NOISE.append(skia.Image.fromarray(rgba, colorType=skia.kRGBA_8888_ColorType))


def room(cv, t, light):
    vgrad(cv, (0, 0, W, H), [C("#15110f"), C("#221a17"), C("#0b0908")])
    # tahta
    bx, by, bw, bh = 70, 520, 940, 1060
    rrect(cv, bx - 26, by - 26, bw + 52, bh + 52, 14, C("#3b2716"), outline=False)
    rrect(cv, bx, by, bw, bh, 8, C("#1f2e26"), outline=False)
    rnd = random.Random(5)
    for _ in range(26):   # silinmiş tebeşir lekeleri
        x, y = rnd.uniform(bx + 40, bx + bw - 40), rnd.uniform(by + 40, by + bh - 40)
        cv.drawOval(skia.Rect.MakeXYWH(x - 120, y - 30, 240, 60), fill(C("#d8e0d8", 10), blur=20))
    cv.drawRect(skia.Rect.MakeXYWH(bx - 26, by + bh + 26, bw + 52, 24), fill(C("#2b1c10")))
    # tahtaya kazınmış "yardım et"
    f = skia.Font(F_CHALK, 40)
    cv.save()
    cv.rotate(-8)
    cv.drawString("yardım et", 780, 1650, f, fill(C("#d0d0c8", 28)))
    cv.restore()
    # ampul (sallanan)
    ang = math.sin(t * 1.25) * 9
    cv.save()
    cv.translate(W / 2, 0)
    cv.rotate(ang)
    cv.drawLine(0, 0, 0, 300, stroke(C("#0a0a0a"), 5))
    rrect(cv, -22, 290, 44, 40, 6, C("#2a2a2a"), outline=False)
    cv.drawCircle(0, 358, 38, fill(C("#fff2c2", int(60 + 195 * light))))
    if light > 0.05:
        glow(cv, 0, 358, 220, C("#ffd98a"), int(200 * light))
    cv.restore()
    rad = math.radians(ang)
    return (W / 2 - math.sin(rad) * 358, math.cos(rad) * 358)


def darkness(cv, light, lx, ly):
    """Işık havuzu: ampul çevresi aydınlık, kenarlar karanlık; ışık sönünce her şey kararır."""
    a_in = int(255 * (1 - light) * 0.92)
    a_out = int(255 * min(1, 0.72 + (1 - light) * 0.3))
    sh = skia.GradientShader.MakeRadial(skia.Point(lx, ly + 500), 1500,
                                        [C("#000000", a_in), C("#000000", a_out)], [0.15, 1.0])
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))


def figure(cv, x, y, s, alpha, eyes=1.0):
    """Gölge figür: uzun, ince, kırmızı gözler."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    p = skia.Paint(Color=C("#050505", alpha), AntiAlias=True)
    p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 6))
    cv.drawOval(skia.Rect.MakeXYWH(-70, -560, 140, 170), p)
    path = skia.Path()
    path.moveTo(-60, -420)
    path.cubicTo(-160, -200, -140, 100, -110, 400)
    path.lineTo(110, 400)
    path.cubicTo(140, 100, 160, -200, 60, -420)
    path.close()
    cv.drawPath(path, p)
    for sx in (-26, 26):   # uzun kollar
        cv.drawLine(sx * 3, -380, sx * 5.5, 150, skia.Paint(Color=C("#050505", alpha), StrokeWidth=26,
                    Style=skia.Paint.kStroke_Style, StrokeCap=skia.Paint.kRound_Cap, AntiAlias=True))
    if eyes > 0:
        for sx in (-24, 24):
            glow(cv, sx, -490, 40, C("#ff0000"), int(alpha * eyes))
            cv.drawOval(skia.Rect.MakeXYWH(sx - 10, -496, 20, 10), fill(C("#ff2020", int(alpha * eyes))))
    cv.restore()


def frame(cv, t):
    light = flicker(t)
    shake = 0.0
    near = min(abs(t - s) for s in SCARES)
    if near < 0.35:
        shake = (0.35 - near) * 40
    cv.save()
    cv.translate(random.Random(int(t * 60)).uniform(-shake, shake), random.Random(int(t * 60) + 1).uniform(-shake, shake))
    lx, ly = room(cv, t, light)

    # ---- başlık sahnesi
    if t < 5.0:
        k = ease(clamp((t - 0.6) / 1.5))
        col = C("#b30000", int(255 * k))
        creep_title(cv, "BERNOULLİ", W / 2, 860, 150, col, t)
        creep_title(cv, "DİFERANSİYEL", W / 2, 1060, 104, col, t)
        creep_title(cv, "DENKLEMİ", W / 2, 1220, 104, col, t)
        text_c(cv, "bu gece çözülecek...", W / 2, 1400, 48, C("#d9d4c7", int(200 * clamp((t - 2.5) / 1))), F_TYPE)

    # ---- adımlar
    for a, b, title, lines in STEPS:
        if a <= t < b:
            lt = t - a
            text_c(cv, title, W / 2, 640, 54 if len(title) < 22 else 44, C("#ff4040", int(80 + 175 * light)), F_TYPE)
            n = len(lines)
            span = (b - a - 1.2) / n
            ys = np.linspace(860, 1400, n) if n > 1 else [1010]
            for i, (ln, sz) in enumerate(lines):
                rv = clamp((lt - 0.4 - i * span) / min(1.8, max(0.9, span * 0.55)))
                draw_chalk(cv, ln, W / 2, ys[i], sz, rv, light, t, seed=i + int(a))
            if title.startswith("ÖRNEK") and lt > 8.0:   # cevap kutusu
                k = clamp((lt - 8.0) / 0.4)
                rrect(cv, 110, ys[-1] - 95, W - 220, 140, 20, C("#ff2a2a", int(255 * k)), outline=False)
                rrect(cv, 116, ys[-1] - 89, W - 232, 128, 16, C("#1f2e26", int(255 * k)), outline=False)
                draw_chalk(cv, lines[-1][0], W / 2, ys[-1], lines[-1][1], 1.0, light, t, seed=99)

    # ---- final: sıra sende
    if t >= 46.2:
        lt = t - 46.2
        creep_title(cv, "SIRA SENDE...", W / 2, 820, 120, C("#c00000"), t)
        draw_chalk(cv, "y′ − y = eˣ·y²", W / 2, 1060, 96, clamp(lt / 1.6), light, t, seed=7)
        text_c(cv, "çözemezsen...", W / 2, 1300, 58, C("#e0dccf", int(255 * clamp((lt - 1.8) / 0.8))), F_TYPE)
        if lt > 3.0:
            text_c(cv, "O GELECEK", W / 2, 1400, 74, C("#ff2020", int(255 * clamp((lt - 3.0) / 0.4))), F_TYPE)

    # ---- gölge figür: karartmalarda ve titremelerde belirir
    fig_a = 0
    if 33.0 < t < 45.0 and light < 0.4:
        fig_a = 200
    if 44.9 < t < 46.2:
        fig_a = 230
    if fig_a:
        fs = 1.0 if t < 44.9 else lerp(1.0, 1.6, clamp((t - 44.9) / 1.3))
        figure(cv, 900 - (t > 44.9) * 300 * clamp((t - 44.9) / 1.3), 1500, fs, fig_a)
    darkness(cv, light, lx, ly)
    # karanlıkta sadece kırmızı parlayan yazılar görünsün
    if light < 0.3:
        for a, b, title, lines in STEPS:
            if a <= t < b:
                text_c(cv, title, W / 2, 640, 44, C("#ff2020", 140), F_TYPE)
    cv.restore()

    # ---- jump scare (50.6 - 51.25): yüz
    if 50.6 <= t < 51.25:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#1a0000")))
        glow(cv, W / 2, H / 2, 1100, C("#ff0000"), 120)
        k = clamp((t - 50.6) / 0.1)
        jit = random.Random(int(t * 90))
        cv.save()
        cv.translate(W / 2 + jit.uniform(-25, 25), H / 2 - 60 + jit.uniform(-25, 25))
        cv.scale(1.5 + 0.9 * k, 1.5 + 0.9 * k)
        cv.rotate(jit.uniform(-4, 4))
        face = skia.Path()                       # uzun, çökük, solgun yüz
        face.moveTo(0, -360)
        face.cubicTo(230, -350, 250, -40, 170, 200)
        face.cubicTo(110, 360, -110, 360, -170, 200)
        face.cubicTo(-250, -40, -230, -350, 0, -360)
        cv.drawPath(face, fill(C("#cfc6b8")))
        cv.drawPath(face, fill(C("#5a4a40", 90), blur=40))
        for sx in (-95, 95):                    # oyuk, akan gözler
            eye = skia.Path()
            eye.moveTo(sx - 70, -110)
            eye.quadTo(sx, -190, sx + 70, -110)
            eye.quadTo(sx + 40, -10, sx, 0)
            eye.quadTo(sx - 40, -10, sx - 70, -110)
            cv.drawPath(eye, fill(C("#050000")))
            cv.drawLine(sx - 20, -10, sx - 26, 150, stroke(C("#050000"), 16))
            cv.drawLine(sx + 22, -12, sx + 30, 90, stroke(C("#050000"), 10))
            cv.drawCircle(sx, -80, 9, fill(C("#ff1010")))
            glow(cv, sx, -80, 40, C("#ff0000"), 220)
        mouth = skia.Path()                      # yırtık, dişli ağız
        mouth.moveTo(-150, 130)
        mouth.quadTo(0, 90, 150, 130)
        mouth.quadTo(40, 340, 0, 345)
        mouth.quadTo(-40, 340, -150, 130)
        cv.drawPath(mouth, fill(C("#0a0000")))
        for i in range(9):
            x0 = -120 + i * 30
            cv.drawPath(skia.Path().moveTo(x0, 122).lineTo(x0 + 14, 170).lineTo(x0 + 28, 120).close(),
                        fill(C("#e8e0c8")))
        cv.restore()
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#ff0000", int(60 * (1 - k)))))
    if t >= 51.25:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#000000")))
        a = int(255 * clamp((t - 51.6) / 0.6))
        creep_title(cv, "BERNOULLİ", W / 2, 980, 110, C("#8a0000", a), t, drip=False)

    # ---- film greni, kırmızı ton, vinyet
    img = NOISE[int(t * 24) % len(NOISE)]
    p = skia.Paint(Alphaf=0.10, BlendMode=skia.BlendMode.kOverlay)
    cv.drawImageRect(img, skia.Rect.MakeWH(W, H), skia.SamplingOptions(), p)
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#5a0000", 35)))
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.72,
                                        [C("#000000", 0), C("#000000", 230)], [0.5, 1.0])
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))
    # glitch: stinger anlarında kırmızı/camgöbeği kayma bandı
    if near < 0.12:
        y0 = random.Random(int(t * 100)).uniform(300, 1600)
        cv.drawRect(skia.Rect.MakeXYWH(0, y0, W, 40), fill(C("#ff0040", 70)))
        cv.drawRect(skia.Rect.MakeXYWH(0, y0 + 50, W, 18), fill(C("#00ffff", 50)))


# ============================================================== korku müziği
def music():
    from pedalboard import Pedalboard, Reverb, LowpassFilter, HighpassFilter
    n = int(TOTAL * SR)
    t = np.arange(n) / SR
    rng = np.random.default_rng(3)

    def saw(f, ph=0.0):
        return 2 * ((t * f + ph) % 1.0) - 1

    out = np.zeros((2, n), np.float32)
    # 1) alçak drone: C2 + C#2 (küçük ikili, uyumsuz) + 32 Hz uğultu
    drone = (saw(65.41) + saw(69.30, 0.3) + 0.6 * saw(65.6, 0.6)) / 3
    drone = LowpassFilter(320)(drone.astype(np.float32)[None], SR)[0]
    drone *= 0.55 + 0.25 * np.sin(2 * np.pi * 0.07 * t)
    sub = np.sin(2 * np.pi * 32.7 * t) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * t))
    bed = drone * 0.28 + sub * 0.22
    # 2) gerilim yayları: tremololu yüksek küme, her adımın sonuna doğru kabarır
    swell = np.zeros(n)
    for s in SCARES:
        a = int((s - 3.0) * SR)
        b = int(s * SR)
        if a > 0:
            swell[a:b] = np.linspace(0, 1, b - a) ** 2
    trem = 0.6 + 0.4 * np.sin(2 * np.pi * 9 * t)
    strings = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) for f in (523.25, 554.37, 783.99, 830.6)) / 4
    strings = strings * trem * (0.15 + 0.85 * swell) * 0.10
    # 3) müzik kutusu: ürkütücü ninni (do minör, hafif detune), iki kez çalar
    melody = [72, 75, 74, 72, 71, 72, 67, 68, 72, 75, 79, 78, 77, 75, 74, 71]
    box = np.zeros(n)
    for rep_start in (5.5, 29.5):
        for i, m in enumerate(melody):
            st = rep_start + i * 0.42
            if st >= TOTAL:
                break
            f = 440 * 2 ** ((m - 69) / 12) * (1 + 0.004 * np.sin(i))
            L = int(1.6 * SR)
            tt = np.arange(L) / SR
            note = (np.sin(2 * np.pi * f * tt) + 0.35 * np.sin(2 * np.pi * f * 2.76 * tt)
                    + 0.15 * np.sin(2 * np.pi * f * 5.4 * tt)) * np.exp(-tt * 3.2)
            i0 = int(st * SR)
            box[i0:i0 + L] += note[: max(0, min(L, n - i0))] * 0.13
    # 4) stinger'lar: uyumsuz bakır vuruşu + boom + öncesinde ters süpürme
    stings = np.zeros(n)
    for s in SCARES:
        i0 = int(s * SR)
        L = int(2.2 * SR)
        tt = np.arange(L) / SR
        hit = sum(2 * ((tt * f) % 1) - 1 for f in (130.8, 138.6, 185.0, 196.0)) / 4 * np.exp(-tt * 2.2)
        boom = np.sin(2 * np.pi * (55 * np.exp(-tt * 3) + 28) * tt) * np.exp(-tt * 2.5)
        x = (hit * 0.5 + boom * 0.9)
        big = 1.6 if s >= 50 else 1.0
        stings[i0:i0 + L] += x[: max(0, min(L, n - i0))] * 0.5 * big
        # ters süpürme (1 sn önce)
        a = int((s - 1.0) * SR)
        if a > 0:
            m = i0 - a
            nz = rng.standard_normal(m) * np.linspace(0, 1, m) ** 3
            stings[a:i0] += HighpassFilter(800)(nz.astype(np.float32)[None], SR)[0] * 0.12
    # 5) son bölümde hızlanan kalp atışı
    heart = np.zeros(n)
    k = 44.0
    while k < 50.5:
        bpm = lerp(70, 160, (k - 44) / 6.5)
        for off, g in ((0.0, 1.0), (0.17, 0.7)):
            i0 = int((k + off) * SR)
            L = int(0.25 * SR)
            tt = np.arange(L) / SR
            heart[i0:i0 + L] += np.sin(2 * np.pi * 50 * tt) * np.exp(-tt * 22) * g * 0.7
        k += 60 / bpm
    # 6) ampul vızıltısı (ışık açıkken), çok hafif
    lights = np.array([flicker(x) for x in np.arange(0, TOTAL, 1 / 200)])
    lights = np.interp(t, np.arange(len(lights)) / 200, lights)
    buzz = (np.sign(np.sin(2 * np.pi * 120 * t)) * 0.3 + np.sin(2 * np.pi * 240 * t)) * lights * 0.012
    # 7) jump scare çığlığı (gürültü + yükselen tiz)
    scream = np.zeros(n)
    i0, L = int(50.6 * SR), int(0.8 * SR)
    tt = np.arange(L) / SR
    sc = (rng.standard_normal(L) * 0.5 + np.sin(2 * np.pi * (900 + 1400 * tt) * tt)) * np.exp(-tt * 3)
    scream[i0:i0 + L] = HighpassFilter(600)(sc.astype(np.float32)[None], SR)[0] * 0.5

    mono = bed + strings + box + heart + buzz
    # final karartmada sessizlik (jump scare'den sonra)
    mono[int(51.3 * SR):] *= np.linspace(1, 0, n - int(51.3 * SR)) ** 3
    st = np.stack([mono + stings + scream, mono + stings + scream]).astype(np.float32)
    # stereo: müzik kutusu ve yaylar hafif yanlara
    st[0] += (box * 0.4).astype(np.float32)
    st[1] += (strings * 0.4).astype(np.float32)
    wet = Pedalboard([Reverb(room_size=0.85, damping=0.4, wet_level=0.45, dry_level=0.75, width=1.0)])(st, SR)
    wet = wet / (np.abs(wet).max() + 1e-9) * 0.89
    return wet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, "output")
    surface = skia.Surface(W, H)
    if args.preview is not None:
        for t in args.preview:
            cv = surface.getCanvas()
            cv.clear(C("#000000"))
            frame(cv, t)
            surface.makeImageSnapshot().save(os.path.join(out_dir, f"preview_{t:05.1f}.png"), skia.kPNG)
        return
    import soundfile as sf
    wav = os.path.join(ROOT, "build", "bernoulli.wav")
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    sf.write(wav, music().T, SR, subtype="PCM_16")
    out = os.path.join(out_dir, "bernoulli_korku.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=14", "-c:a", "aac",
                           "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        cv = surface.getCanvas()
        cv.clear(C("#000000"))
        frame(cv, i / FPS)
        arr = surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        ff.stdin.write(np.ascontiguousarray(arr).tobytes())
        if i % 300 == 0:
            print(f"  kare {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("Video hazır:", out)


if __name__ == "__main__":
    main()
