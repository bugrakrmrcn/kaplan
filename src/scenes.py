"""Sahneler: arka planlar, kamera hareketleri ve karakter animasyonları."""
import math
import random

import skia

from gfx import (C, OUTLINE, Arda, Girl, Soldier, circle, clamp, ease, ease_out_back, fill, glow, lerp,
                 limb, pose_bent, pose_mix, pose_run, pose_stand, pose_walk, poly, rrect, shade, stroke, text,
                 vgrad, vignette, FONT_BOLD, SKIN)

W, H = 1080, 1920
GY = 1540  # kaldırım (ayak) çizgisi

ARDA = Arda()
GIRL = Girl()
SOLDIERS = [Soldier(1), Soldier(2), Soldier(3)]


# ======================================================================= kamera
def camera(cv, zoom=1.0, cx=W / 2, cy=H / 2, shake=0.0, t=0.0, rot=0.0):
    sx = (math.sin(t * 53.1) + math.sin(t * 31.7)) * shake
    sy = (math.cos(t * 47.3) + math.sin(t * 27.9)) * shake
    cv.translate(W / 2 + sx, H / 2 + sy)
    cv.rotate(rot)
    cv.scale(zoom, zoom)
    cv.translate(-cx, -cy)


# ======================================================================= Çorum sokağı
def _buildings():
    rnd = random.Random(42)
    out, x = [], -3000
    palette = ["#c9a27e", "#b5846b", "#8f9aa6", "#d1b48c", "#a7795f", "#9aa58e", "#c4b6a2"]
    while x < 9000:
        w = rnd.randint(300, 460)
        h = rnd.randint(780, 1180)
        out.append(dict(x=x, w=w, h=h, col=rnd.choice(palette), seed=rnd.random(), roof=rnd.random() < 0.4))
        x += w + rnd.randint(0, 30)
    return out


BUILDINGS = _buildings()


def sky(cv, mood):
    if mood == "dusk":
        vgrad(cv, (-4000, -1000, 16000, GY + 1000), [C("#2c2f5c"), C("#7a4f74"), C("#e48a5c"), C("#f4b26b")],
              [0.0, 0.45, 0.75, 1.0])
    elif mood == "night":
        vgrad(cv, (-4000, -1000, 16000, GY + 1000), [C("#0e1226"), C("#1e2547"), C("#3b3360")], [0, 0.6, 1])
    elif mood == "red":
        vgrad(cv, (-4000, -1000, 16000, GY + 1000), [C("#1a0d16"), C("#4a1a26"), C("#7a2e2e")], [0, 0.6, 1])


def clock_tower(cv, x, base, dark):
    """Çorum Saat Kulesi silüeti (uzakta)."""
    col = dark
    rrect(cv, x - 70, base - 760, 140, 760, 6, col, outline=False)
    rrect(cv, x - 90, base - 820, 180, 70, 8, shade(col, 1.1), outline=False)
    poly(cv, [(x - 85, base - 820), (x, base - 980), (x + 85, base - 820)], shade(col, 1.15), outline=False)
    cv.drawCircle(x, base - 640, 46, fill(C("#f6e3b0", 230)))
    glow(cv, x, base - 640, 120, C("#ffd27a"), 70)
    cv.drawLine(x, base - 640, x, base - 672, stroke(C("#3a2c22"), 6))
    cv.drawLine(x, base - 640, x + 22, base - 630, stroke(C("#3a2c22"), 6))
    for i in range(4):
        cv.drawRect(skia.Rect.MakeXYWH(x - 50 + i * 28, base - 500, 14, 40), fill(shade(col, 0.7)))


def street(cv, scroll=0.0, mood="dusk", shop=None, lit=0.6, empty_cars=True):
    sky(cv, mood)
    dark_far = {"dusk": C("#5b4466"), "night": C("#252a46"), "red": C("#3a1824")}[mood]
    # uzak silüet + saat kulesi (paralaks 0.3)
    cv.save()
    cv.translate(-scroll * 0.3, 0)
    rnd = random.Random(3)
    x = -2500
    while x < 6000:
        w = rnd.randint(200, 380)
        h = rnd.randint(300, 650)
        cv.drawRect(skia.Rect.MakeXYWH(x, GY - 160 - h, w, h + 10), fill(dark_far))
        x += w
    clock_tower(cv, 820, GY - 120, shade(dark_far, 0.8))
    cv.restore()

    tint = {"dusk": 0.82, "night": 0.45, "red": 0.5}[mood]
    cv.save()
    cv.translate(-scroll, 0)
    for b in BUILDINGS:
        bx, bw, bh = b["x"], b["w"], b["h"]
        if bx + bw < scroll - 800 or bx > scroll + W + 800:
            continue
        col = shade(C(b["col"]), tint)
        top = GY - 60 - bh
        rrect(cv, bx, top, bw, bh + 60, 4, col)
        cv.drawRect(skia.Rect.MakeXYWH(bx - 10, top - 22, bw + 20, 30), fill(shade(col, 0.75)))
        cv.drawRect(skia.Rect.MakeXYWH(bx - 10, top - 22, bw + 20, 30), stroke(OUTLINE, 5))
        rnd = random.Random(int(b["seed"] * 1e6))
        cols = max(2, int((bw - 40) // 105))
        rows = int((bh - 260) // 150)
        gx = (bw - cols * 70) / (cols + 1)
        for r in range(rows):
            for c in range(cols):
                wx = bx + gx + c * (70 + gx)
                wy = top + 60 + r * 150
                on = rnd.random() < lit
                wc = C("#ffd98a") if on else shade(C("#2d3550"), tint + 0.3)
                rrect(cv, wx, wy, 70, 96, 4, wc, lw=4)
                cv.drawLine(wx + 35, wy, wx + 35, wy + 96, stroke(OUTLINE, 3))
                if on:
                    glow(cv, wx + 35, wy + 48, 90, C("#ffcf70"), 45)
        # kapı
        rrect(cv, bx + bw / 2 - 45, GY - 200, 90, 170, 6, shade(col, 0.55))
    # leblebici dükkânı
    if shop is not None:
        sx = shop
        rrect(cv, sx, GY - 520, 560, 490, 6, C("#b5544a") if mood == "dusk" else C("#6a2a2a"))
        rrect(cv, sx + 20, GY - 500, 520, 110, 10, C("#7a1f1f"))
        text(cv, "LEBLEBİCİ", sx + 280, GY - 418, 74, C("#ffd34d"), outline=8)
        for i in range(8):
            colr = C("#e74c3c") if i % 2 == 0 else C("#f5f0e6")
            poly(cv, [(sx + i * 70, GY - 380), (sx + i * 70 + 70, GY - 380), (sx + i * 70 + 80, GY - 320),
                      (sx + i * 70 - 10, GY - 320)], colr, lw=4)
        rrect(cv, sx + 40, GY - 300, 480, 250, 8, C("#ffe9b8"))
        glow(cv, sx + 280, GY - 180, 380, C("#ffd27a"), 90)
        for j in range(3):  # leblebi çuvalları
            bx = sx + 90 + j * 150
            rrect(cv, bx, GY - 170, 110, 110, 30, C("#d8b47a"))
            for k in range(12):
                circle(cv, bx + 18 + (k % 6) * 15, GY - 170 + (k // 6) * 12, 10, C("#f2d27a"), lw=2)
    # sokak lambaları
    for lx in range(-2800, 9000, 760):
        if lx < scroll - 300 or lx > scroll + W + 300:
            continue
        cv.drawLine(lx, GY + 10, lx, GY - 760, stroke(C("#2a2a30"), 16))
        cv.drawLine(lx, GY - 760, lx + 70, GY - 790, stroke(C("#2a2a30"), 12))
        rrect(cv, lx + 50, GY - 800, 60, 26, 8, C("#ffe7a8"))
        glow(cv, lx + 80, GY - 760, 360 if mood != "dusk" else 240, C("#ffd27a"), 90 if mood != "dusk" else 50)
    cv.restore()

    # kaldırım ve yol
    cv.drawRect(skia.Rect.MakeXYWH(-4000, GY - 40, 16000, 110), fill(shade(C("#b9b2a6"), tint + 0.1)))
    cv.save()
    cv.translate(-scroll % 160, 0)
    for i in range(-30, 120):
        cv.drawLine(i * 160 - 2000, GY - 40, i * 160 - 2000, GY + 70, stroke(shade(C("#8d867b"), tint + 0.1), 4))
    cv.restore()
    cv.drawRect(skia.Rect.MakeXYWH(-4000, GY + 70, 16000, 24), fill(shade(C("#d8d2c6"), tint)))
    cv.drawRect(skia.Rect.MakeXYWH(-4000, GY + 94, 16000, 1200), fill(shade(C("#3a3c42"), tint + 0.2)))
    cv.save()
    cv.translate(-scroll % 300, 0)
    for i in range(-20, 60):
        cv.drawRect(skia.Rect.MakeXYWH(i * 300 - 2000, GY + 230, 160, 18), fill(C("#e8e3d0", 200)))
    cv.restore()


def barrier(cv, x, y, s=1.0):
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    for lx in (-160, 160):
        rrect(cv, lx - 10, -160, 20, 160, 4, C("#555555"))
    rrect(cv, -220, -170, 440, 50, 8, C("#f2f2f2"))
    for i in range(5):
        poly(cv, [(-200 + i * 90, -170), (-160 + i * 90, -170), (-200 + i * 90 + 30, -120), (-240 + i * 90 + 30, -120)],
             C("#d63a3a"), outline=False)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-220, -170, 440, 50), 8, 8), stroke(OUTLINE, 6))
    cv.restore()


def siren_lights(cv, t, alpha=80):
    a = int(alpha * (0.5 + 0.5 * math.sin(t * 9)))
    b = int(alpha * (0.5 - 0.5 * math.sin(t * 9)))
    glow(cv, 0, 400, 900, C("#ff2a2a"), a)
    glow(cv, W, 400, 900, C("#2a5bff"), b)


# ======================================================================= yakın planlar
def phone_closeup(cv, t, banner_t, shake):
    vgrad(cv, (0, 0, W, H), [C("#2a2140"), C("#5b3a55"), C("#c0705a")], [0, 0.6, 1])
    for i in range(14):  # bulanık bokeh ışıkları
        rnd = random.Random(i)
        glow(cv, rnd.uniform(0, W), rnd.uniform(200, 1500), rnd.uniform(60, 160), C("#ffcf80"), 90)
    sx = (math.sin(t * 70) * 8) * shake
    cv.save()
    cv.translate(W / 2 + sx, 980)
    cv.rotate(-6 + math.sin(t * 60) * 1.5 * shake)
    # el (arkada)
    circle(cv, -260, 330, 120, SKIN)
    # telefon
    rrect(cv, -270, -560, 540, 1100, 70, C("#121216"))
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-248, -538, 496, 1056), 54, 54)
    cv.save()
    cv.clipRRect(rr, True)
    vgrad(cv, (-248, -538, 496, 1056), [C("#1f3b6b"), C("#5b3f8a"), C("#c46b8a")])
    text(cv, "21:47", 0, -330, 150, C("#ffffff"), font=FONT_BOLD)
    text(cv, "Salı, 10 Kasım", 0, -250, 40, C("#ffffff", 220))
    # bildirim kartı
    if banner_t > 0:
        y = lerp(-700, -190, ease_out_back(banner_t))
        rrect(cv, -225, y, 450, 230, 34, C("#f4f4f6", 245), outline=False)
        rrect(cv, -200, y + 24, 56, 56, 14, C("#e53935"), outline=False)
        poly(cv, [(-172, y + 34), (-154, y + 68), (-190, y + 68)], C("#ffffff"), outline=False)
        cv.drawLine(-172, y + 46, -172, y + 58, stroke(C("#e53935"), 5))
        text(cv, "ACİL DURUM UYARISI", -128, y + 50, 27, C("#222222"), align="left")
        text(cv, "şimdi", 200, y + 92, 24, C("#888888"), align="right")
        text(cv, "Sakın sokağa", -200, y + 130, 50, C("#c62828"), align="left")
        text(cv, "çıkmayın!", -200, y + 190, 50, C("#c62828"), align="left")
    cv.restore()
    rrect(cv, -60, -520, 120, 34, 17, C("#000000"), outline=False)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-270, -560, 540, 1100), 70, 70), stroke(OUTLINE, 8))
    # parmaklar (önde)
    for i in range(3):
        rrect(cv, 200, -120 + i * 120, 120, 90, 45, SKIN)
    rrect(cv, -330, 160, 150, 90, 45, SKIN)
    cv.restore()
    # Arda'nın eşofman kolu
    limb(cv, (-60 + sx, 1900), (180 + sx, 1400), 230, C("#1f2127"), stripes=True)


def watch_closeup(cv, t, bpm, beat):
    vgrad(cv, (0, 0, W, H), [C("#140c14"), C("#3a1420"), C("#5a1a22")])
    for i in range(10):
        rnd = random.Random(i + 20)
        glow(cv, rnd.uniform(0, W), rnd.uniform(100, 1700), rnd.uniform(80, 200), C("#ff6040"), 60)
    cv.save()
    cv.translate(W / 2, 860)
    cv.rotate(-14)
    # kol
    limb(cv, (-900, 40), (-180, 20), 300, C("#1f2127"), stripes=True)
    rrect(cv, -200, -120, 900, 270, 130, SKIN)
    circle(cv, 600, 15, 120, SKIN, outline=False)
    # kayış
    rrect(cv, -80, -240, 220, 510, 30, C("#2b2b2f"))
    # saat gövdesi
    sc = 1 + beat * 0.03
    cv.scale(sc, sc)
    rrect(cv, -150, -190, 380, 410, 90, C("#3a3a40"))
    rrect(cv, -128, -168, 336, 366, 74, C("#050505"), outline=False)
    rrect(cv, 228, -40, 24, 80, 10, C("#5a5a60"))
    hx, hy = 30, -60
    hs = 1 + beat * 0.25
    p = skia.Path()
    p.moveTo(hx, hy + 40 * hs)
    p.cubicTo(hx - 70 * hs, hy - 10 * hs, hx - 30 * hs, hy - 60 * hs, hx, hy - 25 * hs)
    p.cubicTo(hx + 30 * hs, hy - 60 * hs, hx + 70 * hs, hy - 10 * hs, hx, hy + 40 * hs)
    cv.drawPath(p, fill(C("#ff2d3d")))
    glow(cv, hx, hy, 160, C("#ff2d3d"), int(80 + beat * 120))
    text(cv, f"{int(bpm)}", 30, 110, 120, C("#ffffff") if bpm < 150 else C("#ff4d4d"))
    text(cv, "BPM", 30, 165, 40, C("#bbbbbb"))
    cv.restore()
    if bpm >= 160:
        a = int(255 * (0.5 + 0.5 * math.sin(t * 12)))
        rrect(cv, 180, 380, 720, 110, 30, C("#e53935", a), outline=False)
        text(cv, "YÜKSEK NABIZ!", W / 2, 455, 56, C("#ffffff", a))


def alley(cv, t, light_on=1.0):
    vgrad(cv, (-3000, -500, 9000, GY + 500), [C("#121528"), C("#1d2140")])
    # tuğla duvar
    rrect(cv, -1500, 300, 5000, GY - 300, 0, C("#5a3a34"), outline=False)
    for r in range(0, 40):
        y = 300 + r * 60
        if y > GY:
            break
        off = (r % 2) * 70
        for c in range(-12, 40):
            x = -1500 + c * 140 + off
            cv.drawRect(skia.Rect.MakeXYWH(x, y, 134, 54), fill(C("#6b463d") if (r * 7 + c) % 5 else C("#5e3d35")))
    vgrad(cv, (-1500, 300, 5000, 400), [C("#000000", 160), C("#000000", 0)])
    # lamba
    lx = 840
    cv.drawLine(lx, GY, lx, 380, stroke(C("#26262c"), 18))
    cv.drawLine(lx, 380, lx - 90, 350, stroke(C("#26262c"), 14))
    rrect(cv, lx - 130, 340, 70, 30, 10, C("#ffe7a8"))
    glow(cv, lx - 95, 380, 700, C("#ffd27a"), int(110 * light_on))
    # ışık konisi
    path = skia.Path()
    path.moveTo(lx - 120, 370)
    path.lineTo(lx - 70, 370)
    path.lineTo(lx + 260, GY + 60)
    path.lineTo(lx - 460, GY + 60)
    path.close()
    sh = skia.GradientShader.MakeLinear([skia.Point(0, 370), skia.Point(0, GY)],
                                        [C("#ffe3a0", int(90 * light_on)), C("#ffe3a0", int(25 * light_on))])
    cv.drawPath(path, skia.Paint(Shader=sh, AntiAlias=True))
    # zemin
    cv.drawRect(skia.Rect.MakeXYWH(-3000, GY - 20, 9000, 800), fill(C("#2b2c33")))
    cv.drawRect(skia.Rect.MakeXYWH(-3000, GY - 20, 9000, 10), fill(C("#46474f")))
    # çöp konteyneri
    rrect(cv, -60, GY - 300, 300, 290, 12, C("#2f5d3a"))
    rrect(cv, -80, GY - 330, 340, 50, 10, C("#244a2e"))


# ======================================================================= sahneler
def scene_hook(cv, t, D, info):
    z = lerp(1.0, 1.18, t / D)
    cv.save()
    camera(cv, z, W / 2, H * 0.52, t=t)
    street(cv, scroll=200 + t * 20, mood="night", lit=0.25)
    cv.restore()
    vignette(cv, W, H, 230)
    a = int(255 * clamp(t / 0.6) * clamp((D - t) / 0.4))
    text(cv, "BÖLÜM 1", W / 2, 360, 54, C("#ff4d4d", a), outline=8, outline_color=C("#000000", a))
    text(cv, "SAKIN SOKAĞA ÇIKMA", W / 2, 450, 76, C("#ffffff", a), outline=10, outline_color=C("#000000", a))


def scene_intro(cv, t, D, info):
    speed = 140
    ax = 300 + t * speed  # Arda dünya koordinatı
    scroll = ax - 430
    z = lerp(1.0, 1.08, t / D)
    cv.save()
    camera(cv, z, W / 2, H * 0.5, t=t)
    street(cv, scroll=scroll, mood="dusk", shop=1500, lit=0.7)
    cv.translate(-scroll, 0)
    phase = t * 2 * math.pi * 0.85
    ARDA.draw(cv, ax, GY, 1.0, 1, pose_walk(phase), bag=1, expr="smile", look=0.5)
    cv.restore()
    # karakter tanıtım etiketi
    li = info["line_starts"]
    if len(li) > 1 and li[1] - 0.3 < t < li[3]:
        k = ease(clamp((t - li[1] + 0.3) / 0.4)) * clamp((li[3] - t) / 0.3)
        a = int(255 * k)
        rrect(cv, 60 - (1 - k) * 80, 240, 470, 150, 24, C("#111111", int(a * 0.75)), outline=False)
        text(cv, "ARDA TÜFEKER", 90 - (1 - k) * 80, 305, 50, C("#ffd34d", a), align="left")
        text(cv, "Çorum • 1.90 m", 90 - (1 - k) * 80, 360, 36, C("#ffffff", a), align="left", font=None)


def scene_notif(cv, t, D, info):
    li = info["line_starts"]
    banner_t = clamp((t - (li[0] + 0.8)) / 0.5)
    shake = 1.0 if (li[0] < t < li[0] + 1.0) else 0.0
    z = lerp(1.0, 1.12, t / D) + (0.12 * ease(clamp((t - li[2]) / 0.25)) if len(li) > 2 else 0)
    cv.save()
    camera(cv, z, W / 2, 900, shake=6 * shake, t=t)
    phone_closeup(cv, t, banner_t, shake)
    cv.restore()
    if len(li) > 2 and t > li[2]:
        k = clamp((t - li[2]) / 0.2)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#ff0000", int(60 * (1 - k)))))
        vignette(cv, W, H, 200, (90, 0, 0))


def scene_look(cv, t, D, info):
    li = info["line_starts"]
    ax = 1500
    z = lerp(1.25, 1.0, ease(t / D))
    cv.save()
    camera(cv, z, ax - 1000, GY - 560, t=t)
    street(cv, scroll=1000, mood="dusk", lit=0.15)
    cv.translate(-1000, 0)
    # baş sağa-sola bakar
    look = math.sin(max(0, t - 0.6) * 2.4) if t < li[1] + 1.5 else -0.8
    expr = "worried" if t < li[1] else "scared"
    head = ARDA.draw(cv, ax, GY, 1.0, 1, pose_stand(t * 2), bag=1, expr=expr, look=look)
    # soru işareti
    if t > 0.8:
        k = ease_out_back(clamp((t - 0.8) / 0.4))
        text(cv, "?", ax + 140, GY - 1160 - k * 30, 160 * k + 1, C("#ffffff"), outline=10)
    cv.restore()
    vignette(cv, W, H, 150)


def scene_soldiers(cv, t, D, info):
    li = info["line_starts"]
    # kamera Arda'dan askerlere kayar
    pan = ease(clamp((t - li[1] + 0.6) / 1.4))
    cx = lerp(560, 1250, pan)
    z = lerp(1.05, 1.25, pan)
    cv.save()
    camera(cv, z, cx, GY - 520, t=t, shake=2 * pan)
    street(cv, scroll=1000, mood="night", lit=0.1)
    cv.translate(-1000, 0)
    ARDA.draw(cv, 1400, GY, 1.0, 1, pose_stand(t * 3), bag=1, expr="scared", look=1.0)
    barrier(cv, 2350, GY, 0.95)
    # askerler köşeden çıkar
    for i, s in enumerate(SOLDIERS):
        enter = ease(clamp((t - li[1] + 0.2 - i * 0.25) / 1.0))
        sx = lerp(2900, 2050 + i * 170, enter)
        moving = 0 < enter < 1
        pose = pose_walk(t * 7 + i, 0.6) if moving else pose_stand(t * 2 + i)
        s.draw(cv, sx, GY + 10 - i * 4, 0.95, -1, pose, look=0.9, aim=0)
    cv.restore()
    siren_lights(cv, t, int(70 * pan))
    vignette(cv, W, H, 190)


def scene_aim(cv, t, D, info):
    aim = ease(clamp((t - 0.6) / 1.2))
    z = lerp(1.0, 1.5, ease(t / D))
    cv.save()
    camera(cv, z, 560, GY - 640, t=t, shake=3 + 4 * aim)
    street(cv, scroll=2600, mood="red", lit=0.05)
    cv.translate(-2600, 0)
    barrier(cv, 3300, GY, 1.0)
    for i, s in enumerate(SOLDIERS[1:], 1):
        s.draw(cv, 3000 + i * 230, GY + 8, 1.0, -1, pose_stand(t * 2 + i), look=0.9, aim=0)
    # öndeki asker silahını doğrultur
    pose = pose_stand(t * 2)
    pose["arms"] = [(lerp(0.06, 1.25, aim), lerp(0.1, 0.25, aim)), (lerp(-0.06, 1.0, aim), lerp(0.1, 0.9, aim))]
    SOLDIERS[0].draw(cv, 3020, GY + 10, 1.1, -1, pose, look=1.0, aim=aim)
    cv.restore()
    siren_lights(cv, t, 90)
    # nişangâh kırmızı lazer noktası
    if aim > 0.9:
        k = clamp((t - 1.9) / 0.3)
        glow(cv, W / 2 - 60, 620, 60, C("#ff0000"), int(220 * k))
        cv.drawCircle(W / 2 - 60, 620, 9, fill(C("#ff2a2a", int(255 * k))))
    vignette(cv, W, H, 230, (60, 0, 0))


def scene_run(cv, t, D, info):
    li = info["line_starts"]
    speed = 620
    ax = 3000 - t * speed
    scroll = ax - 560
    z = 1.05 + 0.03 * math.sin(t * 2)
    cv.save()
    camera(cv, z, W / 2, H * 0.52, t=t, shake=5)
    street(cv, scroll=scroll, mood="night", lit=0.15)
    cv.translate(-scroll, 0)
    phase = t * 2 * math.pi * 1.6
    # saçılan leblebiler
    if len(li) > 2:
        t0 = li[2] - 0.6
        if t > t0:
            rnd = random.Random(5)
            for k in range(40):
                st = t0 + k * 0.05
                if t < st:
                    continue
                dt = t - st
                x0 = 3000 - st * speed + 40
                vx, vy = rnd.uniform(-60, 200), rnd.uniform(-650, -300)
                x = x0 + vx * dt
                y = GY - 560 + vy * dt + 1500 * dt * dt
                y = min(y, GY - 10 + rnd.uniform(-20, 40))
                circle(cv, x, y, 11, C("#f0d27a"), lw=3)
    ARDA.draw(cv, ax, GY, 1.0, -1, pose_run(phase), bag=1 if (len(li) < 3 or t < li[2] - 0.6) else 0,
              expr="scared", look=1.0, mouth=0.8, sweat=(t * 1.5) % 1.0)
    cv.restore()
    # hız çizgileri
    rnd = random.Random(int(t * 12))
    for i in range(14):
        y = rnd.uniform(200, 1700)
        x = rnd.uniform(-100, W)
        cv.drawLine(x, y, x + rnd.uniform(150, 400), y, stroke(C("#ffffff", 60), 4))
    vignette(cv, W, H, 200)
    # "huh huh" baloncukları
    if len(li) > 1 and li[1] - 0.2 < t < (li[2] if len(li) > 2 else D):
        for k in range(3):
            tt = (t - li[1] + k * 0.27) % 0.8
            a = int(255 * (1 - tt / 0.8))
            text(cv, "huh!", W / 2 - 220 - tt * 120, 640 - tt * 140 + k * 60, 54, C("#ffffff", a), outline=7,
                 outline_color=C("#000000", a))


def scene_watch(cv, t, D, info):
    li = info["line_starts"]
    bpm = lerp(96, 187, ease(clamp((t - 0.3) / (li[1] + 0.6 if len(li) > 1 else D))))
    period = 60 / bpm
    beat = math.exp(-((t % period) / period) * 6)
    z = lerp(1.0, 1.15, t / D)
    cv.save()
    camera(cv, z, W / 2, 900, shake=3 if t < 1.0 else 1.5, t=t)
    watch_closeup(cv, t, bpm, beat)
    cv.restore()
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#ff0000", int(35 * beat))))
    vignette(cv, W, H, 220, (40, 0, 0))


def scene_rest(cv, t, D, info):
    z = lerp(1.0, 1.12, t / D)
    cv.save()
    camera(cv, z, W / 2, H * 0.52, t=t)
    alley(cv, t)
    k = ease(clamp(t / 0.8))
    pose = pose_mix(pose_run(t * 9), pose_bent(t * 7), k)
    ARDA.draw(cv, 330 + 80 * (1 - k), GY, 1.0, 1, pose, bag=0, expr="tired", look=0.3, sweat=(t * 0.9) % 1)
    cv.restore()
    vignette(cv, W, H, 180)
    for kk in range(2):
        tt = (t * 1.2 + kk * 0.5) % 1.0
        a = int(200 * (1 - tt))
        text(cv, "huh", 800 + tt * 60, 520 - tt * 100 + kk * 40, 46, C("#ffffff", a), outline=6,
             outline_color=C("#000000", a))


def scene_girl(cv, t, D, info):
    li = info["line_starts"]
    enter = ease(clamp((t - 0.2) / 1.6))
    gx = lerp(1350, 820, enter)
    reveal = clamp((t - li[2] + 0.3) / 0.6) if len(li) > 2 else 0
    stand_k = ease(clamp((t - 0.6) / 0.8))
    zoom_face = ease(clamp((t - li[2]) / 1.4)) if len(li) > 2 else 0
    z = lerp(1.0, 1.75, zoom_face)
    cx = lerp(W / 2, gx - 40, zoom_face)
    cy = lerp(H * 0.52, GY - 760, zoom_face)
    cv.save()
    camera(cv, z, cx, cy, t=t)
    alley(cv, t)
    pose = pose_mix(pose_bent(t * 6), pose_stand(t * 2), stand_k)
    ARDA.draw(cv, 330, GY, 1.0, 1, pose, bag=0, expr="surprised" if stand_k > 0.5 else "tired", look=1.0)
    if stand_k > 0.6:
        k = ease_out_back(clamp((t - 1.2) / 0.3))
        text(cv, "!", 470, GY - 1130, 180 * k + 1, C("#ffd34d"), outline=10)
    gpose = pose_walk(t * 6, 0.7) if enter < 1 else pose_stand(t * 2)
    GIRL.draw(cv, gx, GY, 1.0, -1, gpose, skin=C("#f8dcc0"), look=1.0, expr="neutral")
    cv.restore()
    if reveal < 1:
        # kızın üzerinde karanlık katman (gizem)
        cv.save()
        camera(cv, z, cx, cy, t=t)
        cv.drawOval(skia.Rect.MakeXYWH(gx - 200, GY - 1000, 400, 1060), fill(C("#05060c", int(235 * (1 - reveal))), blur=18))
        cv.restore()
    vignette(cv, W, H, 200)


def scene_end(cv, t, D, info):
    vgrad(cv, (0, 0, W, H), [C("#0a0a12"), C("#1a0f1a")])
    for i in range(12):
        rnd = random.Random(i + 70)
        glow(cv, rnd.uniform(0, W), rnd.uniform(0, H), rnd.uniform(100, 260), C("#ff3040"), 30)
    # kızın siluet yüzü
    a = clamp(t / 1.0)
    cv.save()
    cv.translate(W / 2, 760)
    cv.scale(1.6, 1.6)
    rrect(cv, -114, -40, 228, 230, 60, C("#000000", int(255 * a)), outline=False)
    cv.drawCircle(0, 0, 100, fill(C("#000000", int(255 * a))))
    glow(cv, 0, 0, 150, C("#ff3040"), int(40 * a))
    # sadece gözler parlar
    for sx in (-34, 34):
        cv.drawOval(skia.Rect.MakeXYWH(sx - 9, -4, 18, 24), fill(C("#ffffff", int(230 * a))))
    cv.restore()
    k = ease_out_back(clamp((t - 0.3) / 0.6))
    text(cv, "1. BÖLÜMÜN SONU", W / 2, 330, 84 * k + 1, C("#ffffff"), outline=10)
    li = info["line_starts"]
    if len(li) > 1 and t > li[1]:
        kk = ease_out_back(clamp((t - li[1]) / 0.5))
        rrect(cv, W / 2 - 260 * kk, 1480, 520 * kk + 1, 120, 60, C("#e53950"), outline=False)
        text(cv, "Takip et  +", W / 2, 1562, 58 * kk + 1, C("#ffffff"))
        text(cv, "2. bölüm çok yakında...", W / 2, 1700, 44, C("#ffffff", int(200 * kk)))


SCENE_FUNCS = {
    "hook": scene_hook, "intro": scene_intro, "notif": scene_notif, "look": scene_look,
    "soldiers": scene_soldiers, "aim": scene_aim, "run": scene_run, "watch": scene_watch,
    "rest": scene_rest, "girl": scene_girl, "end": scene_end,
}
