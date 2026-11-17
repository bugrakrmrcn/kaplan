"""Daşşakpaşa şehri — Yigü'nün Audi'siyle şehir turu (çizgi film, dikey video).

Kullanım: python3 tools/edit/dassakpasa.py [--preview 2 8 ...]
Çıktı:    output/dassakpasa.mp4 (1080x1920, 30 fps)
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
import audio  # noqa: E402
from gfx import (C, OUTLINE, SKIN, Figure, circle, clamp, draw_eyes, draw_mouth, ease, ease_out_back, fill,  # noqa: E402
                 glow, lerp, limb, pose_stand, pose_walk, rrect, shade, stroke, text, vgrad, vignette, wrap)

W, H, FPS = 1080, 1920, 30
GY = 1560
SR = audio.SR


# ======================================================================= karakterler
class Yigu(Figure):
    """Sarışın; beyaz 'ami paris' tişört, kot, beyaz spor ayakkabı."""
    thigh, shin, torso = 225, 210, 305
    pants = C("#3d6ea8")
    jacket = C("#fbfbf8")
    shoe = C("#ffffff")
    torso_w = 128
    hair = C("#f2cf63")
    hair_d = C("#c9a23a")

    def draw_arm(self, cv, arm, back, skin):
        S, e, h = arm
        sleeve = shade(self.jacket, 0.88) if back else self.jacket
        mid = (lerp(S[0], e[0], 0.55), lerp(S[1], e[1], 0.55))
        limb(cv, mid, e, self.arm_w * 0.85, shade(skin, 0.95) if back else skin)
        limb(cv, e, h, self.arm_w * 0.8, shade(skin, 0.95) if back else skin)
        limb(cv, S, mid, self.arm_w * 1.25, sleeve)          # kısa kollu tişört
        circle(cv, h[0], h[1], 20, skin)

    def torso_detail(self, cv, w, L):
        # yuvarlak yaka
        cv.drawArc(skia.Rect.MakeXYWH(-30, -L - 46, 60, 50), 20, 140, False, stroke(C("#d9d9d4"), 6))
        # göğüste küçük 'ami paris' yazısı
        f = skia.Font(skia.Typeface.MakeFromFile(os.path.join(ROOT, "assets", "fonts", "Montserrat.ttf")), 21)
        tw = f.measureText("ami paris")
        cv.drawString("ami paris", -tw / 2, -L + 70, f, fill(C("#1a1a1a")))
        # kemer
        cv.drawLine(-w / 2 + 4, -6, w / 2 - 4, -6, stroke(C("#2a2a2a"), 10))

    def draw_head(self, cv, facing, kw):
        r = self.head_r
        expr = kw.get("expr", "smile")
        look = kw.get("look", 0.5)
        circle(cv, -r + 2, 6, 18, SKIN, lw=5)
        circle(cv, r - 2, 6, 18, SKIN, lw=5)
        circle(cv, 0, 0, r, SKIN)
        # hafif sakal gölgesi
        cv.drawArc(skia.Rect.MakeXYWH(-r * 0.75, -r * 0.2, r * 1.5, r * 1.15), 20, 140, False,
                   stroke(C("#d8b878", 120), 14))
        # sarı saç: yana taranmış kabarık perçem
        p = skia.Path()
        p.moveTo(-r - 4, 4)
        p.cubicTo(-r - 18, -r * 1.25, r * 0.4, -r * 1.55, r + 10, -r * 0.55)
        p.cubicTo(r + 22, -r * 0.2, r - 4, 0, r - 8, -10)
        p.cubicTo(r * 0.5, -r * 0.62, -r * 0.2, -r * 0.55, -r * 0.62, -r * 0.35)
        p.cubicTo(-r * 0.8, -r * 0.2, -r * 0.88, -0.05 * r, -r - 4, 4)
        p.close()
        cv.drawPath(p, fill(self.hair))
        cv.drawPath(p, stroke(OUTLINE, 6))
        for i in range(4):   # saç telleri
            q = skia.Path()
            q.moveTo(-r * 0.55 + i * 30, -r * 0.78)
            q.quadTo(-r * 0.2 + i * 34, -r * 1.12, r * 0.25 + i * 26, -r * 0.92)
            cv.drawPath(q, stroke(self.hair_d, 5))
        # kaşlar
        for sx in (-1, 1):
            cv.drawLine(sx * 20 + look * 9, -36, sx * 50 + look * 9, -40 + (2 if sx > 0 else 0), stroke(self.hair_d, 8))
        if kw.get("shades"):
            for sx in (-36, 36):
                rrect(cv, sx - 30 + look * 8, -22, 60, 34, 12, C("#121212"), lw=4)
                cv.drawLine(sx - 16 + look * 8, -14, sx - 4 + look * 8, -14, stroke(C("#ffffff", 120), 4))
            cv.drawLine(-6 + look * 8, -12, 6 + look * 8, -12, stroke(OUTLINE, 5))
        else:
            draw_eyes(cv, look, expr)
        draw_mouth(cv, expr, look, y=52, open_amt=kw.get("mouth", 0.0))


YIGU = Yigu()

PINKS = [C("#f3b7a6"), C("#eaa18f"), C("#f6c8b5"), C("#e9b49a"), C("#d99a85"), C("#f0bfa8")]


def ball_pair(cv, x, y, r, col, face=None, t=0.0, hairs=True, bob=0.0):
    """İki yan yana yuvarlak (şehrin temel yapı taşı). (x, y) = alt orta nokta."""
    yy = y - r + bob
    for sx in (-0.82, 0.82):
        cx = x + sx * r
        circle(cv, cx, yy, r, col, lw=max(3, r * 0.045))
        # parlama
        cv.drawOval(skia.Rect.MakeXYWH(cx - r * 0.55, yy - r * 0.62, r * 0.42, r * 0.26), fill(C("#ffffff", 70)))
    cv.drawLine(x, yy - r * 0.7, x, yy + r * 0.85, stroke(shade(col, 0.75), max(2, r * 0.04)))
    if hairs:   # birkaç komik kıl
        rnd = random.Random(int(x * 7 + r))
        for _ in range(3):
            hx = x + rnd.uniform(-1.4, 1.4) * r
            hy = yy + rnd.uniform(-0.2, 0.6) * r
            q = skia.Path()
            q.moveTo(hx, hy)
            q.quadTo(hx + r * 0.12, hy + r * 0.12, hx + r * 0.05, hy + r * 0.25)
            cv.drawPath(q, stroke(C("#5a3a2a", 160), max(1.5, r * 0.025)))
    if face:
        for sx in (-0.82, 0.82):
            cx = x + sx * r
            s = r / 100
            cv.save()
            cv.translate(cx, yy + r * 0.05)
            cv.scale(s, s)
            draw_eyes(cv, 0.0, face, dx=26, y=-14)
            draw_mouth(cv, "smile" if face != "surprised" else "surprised", 0.0, y=30)
            cv.restore()


def citizen(cv, x, y, s, col, t, wave=0.0, phase=0.0):
    """Daşşakpaşalı vatandaş: çift yuvarlak gövde, kısa bacaklar, el sallayan kollar."""
    bob = -abs(math.sin(t * 6 + phase)) * 12 * s
    r = 70 * s
    for sx in (-1, 1):   # bacaklar
        cv.drawLine(x + sx * r * 0.7, y - 40 * s + bob, x + sx * r * 0.75, y, stroke(OUTLINE, 10 * s))
        cv.drawOval(skia.Rect.MakeXYWH(x + sx * r * 0.75 - 18 * s, y - 10 * s, 36 * s, 16 * s), fill(OUTLINE))
    if wave > 0:   # el sallama
        ang = math.sin(t * 10 + phase) * 0.5
        hx = x + 2.1 * r + math.sin(ang) * 40 * s
        hy = y - 2.3 * r + bob - math.cos(ang) * 40 * s
        cv.drawLine(x + 1.4 * r, y - 1.3 * r + bob, hx, hy, stroke(OUTLINE, 9 * s))
        circle(cv, hx, hy, 14 * s, col, lw=3)
    ball_pair(cv, x, y - 34 * s, r, col, face="happy", t=t, hairs=True, bob=bob)


def building(cv, x, y, r, col, floors, t, seed):
    """Çift yuvarlak bina: alt alta katlar, pencereler, kapı."""
    rnd = random.Random(seed)
    for k in range(floors):
        rr = r * (1 - k * 0.12)
        yy = y - k * rr * 1.55
        ball_pair(cv, x, yy, rr, shade(col, 1 - k * 0.04), hairs=(k == floors - 1))
        for sx in (-0.82, 0.82):
            for j in range(2):
                wx = x + sx * rr + (j - 0.5) * rr * 0.6
                wy = yy - rr * 1.0
                lit = rnd.random() < 0.6
                rrect(cv, wx - rr * 0.13, wy - rr * 0.18, rr * 0.26, rr * 0.34, rr * 0.08,
                      C("#ffe08a") if lit else C("#5a6b82"), lw=3)
    rrect(cv, x - r * 0.22, y - r * 0.62, r * 0.44, r * 0.62, r * 0.2, shade(col, 0.6), lw=4)


def tree(cv, x, y, s):
    cv.drawLine(x, y, x, y - 170 * s, stroke(C("#7a4b2a"), 26 * s))
    ball_pair(cv, x, y - 140 * s, 70 * s, C("#5fbf62"), hairs=False)


def cloud(cv, x, y, s, a=230):
    for sx in (-0.82, 0.82):
        cv.drawCircle(x + sx * 60 * s, y, 60 * s, fill(C("#ffffff", a)))
    cv.drawOval(skia.Rect.MakeXYWH(x - 120 * s, y + 10 * s, 240 * s, 50 * s), fill(C("#ffffff", a)))


def car(cv, x, y, s=1.0, facing=1, wheel=0.0, door=0.0):
    """Yigü'nün gri sedanı (logo çizilmez), plaka 35 YGU 35."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s * facing, s)
    body = C("#5d646e")
    cv.drawOval(skia.Rect.MakeXYWH(-430, -26, 860, 52), fill(C("#000000", 90), blur=10))
    p = skia.Path()
    p.moveTo(-420, -40)
    p.lineTo(-425, -140)
    p.quadTo(-410, -190, -330, -200)
    p.quadTo(-240, -290, -110, -300)
    p.lineTo(60, -300)
    p.quadTo(150, -296, 250, -210)
    p.quadTo(400, -196, 430, -150)
    p.lineTo(436, -40)
    p.close()
    cv.drawPath(p, fill(body))
    cv.drawPath(p, stroke(OUTLINE, 6))
    win = skia.Path()
    win.moveTo(-300, -205)
    win.quadTo(-220, -275, -110, -282)
    win.lineTo(55, -282)
    win.quadTo(130, -276, 210, -210)
    win.close()
    cv.drawPath(win, fill(C("#26323f")))
    cv.drawPath(win, stroke(C("#c9ced6"), 5))
    cv.drawLine(-60, -282, -66, -205, stroke(body, 12))
    cv.drawLine(-200, -150, 380, -150, stroke(shade(body, 1.25), 4))
    rrect(cv, -150, -168, 40, 9, 4, C("#c9ced6"), lw=3)
    rrect(cv, 40, -168, 40, 9, 4, C("#c9ced6"), lw=3)
    # kapı (açılırken)
    if door > 0:
        cv.save()
        cv.translate(-60, -150)
        cv.scale(1 - door * 0.6, 1)
        rrect(cv, 0, -50, 230, 150, 10, shade(body, 0.85), lw=5)
        cv.restore()
    poly_led = [(340, -186), (424, -170), (430, -150), (345, -160)]
    path = skia.Path()
    path.moveTo(*poly_led[0])
    for pt in poly_led[1:]:
        path.lineTo(*pt)
    path.close()
    cv.drawPath(path, fill(C("#e8f2ff")))
    glow(cv, 436, -158, 220, C("#dceaff"), 60)
    rrect(cv, -428, -180, 30, 34, 8, C("#d6283a"))
    rrect(cv, -416, -40, 832, 22, 8, C("#22252a"), lw=4)
    # plaka (arka)
    cv.save()
    cv.translate(-400, -95)
    cv.scale(facing, 1)
    rrect(cv, -12, -16, 24, 32, 3, C("#ffffff"), lw=2)
    cv.restore()
    for wx in (-250, 270):
        cv.save()
        cv.translate(wx, -32)
        circle(cv, 0, 0, 74, C("#141414"))
        circle(cv, 0, 0, 46, C("#b4bac2"), lw=4)
        cv.rotate(math.degrees(wheel))
        for k in range(5):
            a = k * 2 * math.pi / 5
            cv.drawLine(0, 0, math.cos(a) * 42, math.sin(a) * 42, stroke(C("#4a4e55"), 8))
        circle(cv, 0, 0, 10, C("#2a2d33"), lw=3)
        cv.restore()
    cv.restore()


# ======================================================================= arka plan
def sky(cv):
    vgrad(cv, (-2000, -400, 8000, GY + 400), [C("#59b7ff"), C("#9ad7ff"), C("#ffe2b8")], [0, 0.65, 1])


def city(cv, scroll, t, people=True, sign=False):
    sky(cv)
    # güneş (o da çift)
    cv.save()
    cv.translate(-scroll * 0.05, 0)
    glow(cv, 860, 300, 260, C("#ffe27a"), 160)
    ball_pair(cv, 860, 360, 62, C("#ffd34d"), face="happy", hairs=False)
    cv.restore()
    for i, (cx, cy, cs) in enumerate([(200, 220, 0.9), (620, 160, 0.7), (1200, 260, 1.0), (1700, 190, 0.8), (2300, 240, 0.9)]):
        cloud(cv, (cx - scroll * 0.12 + t * 12) % 2600 - 300, cy, cs)
    # uzak siluet (paralaks)
    cv.save()
    cv.translate(-scroll * 0.35, 0)
    for i in range(-4, 40):
        bx = i * 260
        r = 70 + (i * 37 % 50)
        ball_pair(cv, bx, GY - 260, r, C("#c98f86", 150), hairs=False)
        ball_pair(cv, bx + 40, GY - 260 - r * 1.5, r * 0.8, C("#c98f86", 130), hairs=False)
    cv.restore()
    # ana cadde
    cv.save()
    cv.translate(-scroll, 0)
    rnd = random.Random(9)
    x = -600
    i = 0
    while x < 9000:
        r = rnd.randint(85, 120)
        if x > scroll - 600 and x < scroll + W + 600:
            if i % 5 == 2:
                tower(cv, x + 120, GY - 30, t)
            else:
                building(cv, x + r * 1.9, GY - 30, r, PINKS[i % len(PINKS)], rnd.randint(2, 4), t, i)
                if i % 3 == 0:
                    tree(cv, x + r * 3.9, GY - 20, 0.9)
        x += r * 4.2
        i += 1
    if sign:
        welcome_sign(cv, 820, GY - 20, t)
    cv.restore()
    # kaldırım + yol
    cv.drawRect(skia.Rect.MakeXYWH(-2000, GY - 30, 8000, 90), fill(C("#e8d9c4")))
    cv.save()
    cv.translate(-(scroll % 140), 0)
    for k in range(-20, 60):   # kaldırım taşları da yuvarlak
        cv.drawCircle(k * 140, GY + 15, 18, fill(C("#d6c4aa")))
    cv.restore()
    cv.drawRect(skia.Rect.MakeXYWH(-2000, GY + 60, 8000, 900), fill(C("#4b4f57")))
    cv.save()
    cv.translate(-(scroll % 320), 0)
    for k in range(-10, 30):
        rrect(cv, k * 320, GY + 210, 170, 18, 9, C("#f0e8c8"), outline=False)
    cv.restore()


def tower(cv, x, y, t):
    """Daşşak Kulesi: üst üste çiftler, tepede bayrak."""
    for k in range(6):
        r = 100 - k * 12
        ball_pair(cv, x, y - k * 150 + (k * 6), r, PINKS[k % len(PINKS)], hairs=(k == 5))
    top = y - 6 * 150 + 40
    cv.drawLine(x, top, x, top - 130, stroke(OUTLINE, 8))
    wave = math.sin(t * 6) * 10
    path = skia.Path()
    path.moveTo(x, top - 130)
    path.quadTo(x + 60, top - 120 + wave, x + 110, top - 110)
    path.lineTo(x, top - 80)
    path.close()
    cv.drawPath(path, fill(C("#e53935")))
    cv.drawPath(path, stroke(OUTLINE, 4))


def welcome_sign(cv, x, y, t):
    for sx in (-260, 260):
        rrect(cv, x + sx - 14, y - 420, 28, 420, 6, C("#6b4b30"))
    rrect(cv, x - 380, y - 640, 760, 260, 30, C("#2e7d32"))
    rrect(cv, x - 362, y - 622, 724, 224, 22, C("#2e7d32", 0), lw=5)
    cv.drawRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x - 362, y - 622, 724, 224), 22, 22), stroke(C("#ffffff"), 5))
    text(cv, "DAŞŞAKPAŞA'YA", x, y - 545, 70, C("#ffffff"))
    text(cv, "HOŞ GELDİNİZ", x, y - 470, 58, C("#ffffff"))
    text(cv, "Nüfus: hep çift", x, y - 418, 34, C("#ffe27a"))


# ======================================================================= zaman çizelgesi
TOTAL = 30.0
LINES = [   # (başlangıç, metin, konuşmacı, tts metni, hız, perde)
    (0.6, "Burası Daşşakpaşa.", "narrator", None, None, None),
    (2.4, "Bu şehirde her şey yuvarlak... ve hep çift.", "narrator", None, None, None),
    (6.0, "Ve bu şehrin en havalı adamı: Yigü.", "narrator", None, None, None),
    (9.0, "Sarışın, ami paris tişörtlü ve Audi'li.", "narrator", "Sarışın, ami paris tişörtlü ve Audi'li.", None, None),
    (14.4, "Selam Yigü!", "hayriye", None, "+10%", "+18Hz"),
    (15.3, "Hoş geldin abi!", "narrator", None, "+15%", "+12Hz"),
    (17.4, "Sokakta herkes onu tanıyor.", "narrator", None, None, None),
    (23.4, "Daşşakpaşalıyız lan biz!", "arda", "Daşşakpaşalıyız lan biz!", "+4%", "-4Hz"),
]
SUB_SPANS = []   # build_audio doldurur: (a, b, metin, konuşmacı)


def cam_follow(cv, z, cx, cy, shake=0.0, t=0.0):
    sx = (math.sin(t * 53) + math.sin(t * 31)) * shake
    sy = (math.cos(t * 47) + math.sin(t * 27)) * shake
    cv.translate(W / 2 + sx, H / 2 + sy)
    cv.scale(z, z)
    cv.translate(-cx, -cy)


def car_x(t):
    """Araba dünya konumu: 4.5 sn'de girer, 13 sn'de park eder."""
    a, b = 4.5, 13.0
    if t < a:
        return -900.0
    if t > b:
        return 3200.0
    u = (t - a) / (b - a)
    return lerp(-900, 3200, 1 - (1 - u) ** 2)   # sona doğru yavaşla


def frame(cv, t):
    talking = any(a <= t < b for a, b, _, spk in SUB_SPANS if spk == "arda")
    mouth = (0.3 + 0.7 * abs(math.sin(t * 14))) if talking else 0.0

    if t < 4.5:   # açılış: tabela + şehir panoraması
        scroll = lerp(0, 380, ease(t / 4.5))
        z = lerp(1.0, 1.08, t / 4.5)
        cv.save()
        cam_follow(cv, z, W / 2, H * 0.52, t=t)
        city(cv, scroll, t, sign=True)
        cv.translate(-scroll, 0)
        for i, (px, ph) in enumerate([(240, 0), (1240, 1.3), (1500, 2.1)]):
            citizen(cv, px, GY + 20, 0.8, PINKS[i], t, wave=1, phase=ph)
        cv.restore()
        a = int(255 * clamp((t - 0.2) / 0.5))
        text(cv, "DAŞŞAKPAŞA", W / 2, 260, 118, C("#ffe27a", a), outline=14, outline_color=C("#5a2a1a", a), shadow=True)
    elif t < 13.6:   # Audi ile şehir turu
        cx = car_x(t)
        scroll = cx - 420
        cv.save()
        cam_follow(cv, 1.0, W / 2, H * 0.53, t=t, shake=1.5 if t < 12.5 else 0)
        city(cv, scroll, t)
        cv.translate(-scroll, 0)
        for i, (px, ph) in enumerate([(900, 0), (1700, 1.0), (2500, 2.0), (3300, 0.5)]):
            citizen(cv, px, GY + 15, 0.75, PINKS[(i + 2) % 6], t, wave=1, phase=ph)
        car(cv, cx, GY + 175, 1.0, 1, wheel=cx / 74)
        # araba içinde Yigü: kafası ön camdan görünür (cam şekline kırpılır)
        cv.save()
        win = skia.Path()
        win.moveTo(cx - 60, GY + 175 - 282)
        win.lineTo(cx + 55, GY + 175 - 282)
        win.quadTo(cx + 130, GY + 175 - 276, cx + 210, GY + 175 - 210)
        win.lineTo(cx - 60, GY + 175 - 205)
        win.close()
        cv.clipPath(win, skia.ClipOp.kIntersect, True)
        cv.translate(cx + 70, GY + 175 - 222)
        cv.scale(0.58, 0.58)
        YIGU.draw_head(cv, 1, {"expr": "smile", "look": 1.0, "shades": True})
        cv.restore()
        cv.drawPath(win, fill(C("#9fd0ff", 45)))   # cam yansıması
        cv.restore()
        # isim etiketi
        if 6.0 < t < 13.0:
            k = ease(clamp((t - 6.0) / 0.4)) * clamp((13.0 - t) / 0.3)
            a = int(255 * k)
            rrect(cv, 50, 240, 560, 170, 26, C("#111111", int(a * 0.78)), outline=False)
            text(cv, "YİGÜ", 85, 310, 60, C("#ffe27a", a), align="left")
            text(cv, "sarışın · ami paris · Audi", 85, 370, 34, C("#ffffff", a), align="left")
    elif t < 22.6:   # park, iner, yürür; halk selamlar
        lt = t - 13.6
        cx = 3200
        walk = clamp((lt - 1.4) / 7.0)
        yx = lerp(cx + 40, cx + 1500, walk)
        scroll = lerp(cx - 420, yx - 540, ease(clamp((lt - 0.8) / 1.5)))
        cv.save()
        cam_follow(cv, 1.0, W / 2, H * 0.53, t=t)
        city(cv, scroll, t)
        cv.translate(-scroll, 0)
        car(cv, cx, GY + 175, 1.0, 1, door=clamp(lt / 0.5) * clamp((1.6 - lt) / 0.4) if lt < 1.6 else 0)
        for i, (px, ph) in enumerate([(cx + 650, 0), (cx + 950, 0.8), (cx + 1300, 1.6), (cx + 1750, 0.4)]):
            citizen(cv, px, GY + 20, 0.85, PINKS[(i + 1) % 6], t, wave=1 if lt > 0.6 else 0, phase=ph)
        if lt > 0.9:
            pose = pose_walk(t * 6.5, 0.9) if 0 < walk < 1 else pose_stand(t * 2)
            YIGU.draw(cv, yx, GY + 20, 0.95, 1, pose, expr="smile", look=0.8, shades=True)
        cv.restore()
        # konuşma balonları
        for st, msg, bx in ((14.4, "Selam Yigü!", 680), (15.3, "Hoş geldin abi!", 330)):
            if st <= t < st + 2.2:
                k = ease_out_back(clamp((t - st) / 0.25))
                cv.save()
                cv.translate(bx, 760)
                cv.scale(k, k)
                rrect(cv, -190, -60, 380, 110, 40, C("#ffffff"))
                text(cv, msg, 0, 12, 42, C("#1a1a1a"))
                cv.restore()
    else:   # yakın plan: "Daşşakpaşalıyız lan biz!"
        lt = t - 22.6
        zin = ease(clamp(lt / 0.9))
        punch = 0.06 * math.exp(-max(0, lt - 0.8) * 6) if lt > 0.8 else 0
        z = lerp(1.0, 1.9, zin) + punch
        cv.save()
        cam_follow(cv, z, lerp(W / 2, 4760 - 4100, zin), lerp(H * 0.53, GY - 760, zin), t=t,
                   shake=6 * punch / 0.06 if punch else 0)
        city(cv, 4100, t)
        cv.translate(-4100, 0)
        for i, (px, ph) in enumerate([(4250, 0), (4900, 1.0)]):
            citizen(cv, px, GY + 20, 0.85, PINKS[i + 3], t, wave=1, phase=ph)
        pose = pose_stand(t * 2)
        if lt > 0.7:   # yumruk havada
            pose["arms"][0] = (2.25, 0.9)
        YIGU.draw(cv, 4760, GY + 20, 1.0, 1, pose, expr="happy", look=0.0,
                  shades=lt < 0.7, mouth=mouth)
        cv.restore()
        # konfeti
        if lt > 0.8:
            rnd = random.Random(4)
            for k in range(70):
                x0 = rnd.uniform(0, W)
                sp = rnd.uniform(250, 520)
                y = -60 + (lt - 0.8) * sp + rnd.uniform(-300, 0)
                col = [C("#ffd34d"), C("#e53935"), C("#3fcf8e"), C("#6fb1ff"), C("#ff8fb1")][k % 5]
                cv.save()
                cv.translate(x0 + math.sin(lt * 4 + k) * 30, y)
                cv.rotate((lt * 300 + k * 40) % 360)
                cv.drawRect(skia.Rect.MakeXYWH(-9, -5, 18, 10), fill(col))
                cv.restore()
        if lt > 5.2:   # bitiş kartı
            a = int(255 * clamp((lt - 5.2) / 0.5))
            cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#000000", int(a * 0.55))))
            text(cv, "DAŞŞAKPAŞA", W / 2, 820, 120, C("#ffe27a", a), outline=14, outline_color=C("#5a2a1a", a))
            text(cv, "nüfus: hep çift", W / 2, 910, 48, C("#ffffff", a))

    # altyazılar
    for a, b, msg, spk in SUB_SPANS:
        if a <= t < b and spk != "hayriye" and not (msg.startswith("Hoş geldin")):
            big = spk == "arda"
            size = 92 if big else 62
            pop = ease_out_back(clamp((t - a) / 0.18), 2.2)
            lines = wrap(msg, size, W - 120)
            y0 = (1300 if big else 1330) - (len(lines) - 1) * size * 0.6
            cv.save()
            cv.translate(W / 2, y0)
            cv.scale(0.85 + 0.15 * pop, 0.85 + 0.15 * pop)
            cv.translate(-W / 2, -y0)
            if big:
                rrect(cv, W / 2 - 120, y0 - size - 60, 240, 58, 29, C("#ffe27a"), outline=False)
                text(cv, "YİGÜ", W / 2, y0 - size - 18, 38, C("#1a1a1a"))
            for i, ln in enumerate(lines):
                text(cv, ln, W / 2, y0 + i * size * 1.18, size, C("#ffe27a") if big else C("#ffffff"),
                     outline=size * 0.2, outline_color=C("#151515"), shadow=True)
            cv.restore()
    vignette(cv, W, H, 110)
    # geçişlerde kısa kararma
    for cut in (4.5, 13.6, 22.6):
        d = abs(t - cut)
        if d < 0.15:
            cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#000000", int(255 * (1 - d / 0.15)))))
    if t > TOTAL - 0.6:
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#000000", int(255 * clamp((t - TOTAL + 0.6) / 0.6)))))


# ======================================================================= ses
def build_audio():
    n = int(TOTAL * SR)
    out = np.zeros((2, n), np.float32)
    t = np.arange(n) / SR

    def add(sig, at, g=1.0, pan=0.0):
        i = int(at * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        out[0, i:i + len(sig)] += sig * g * (1 - max(pan, 0))
        out[1, i:i + len(sig)] += sig * g * (1 + min(pan, 0))

    # seslendirme
    voice_on = np.zeros(n, np.float32)
    for st, msg, spk, tts_txt, rate, pitch in LINES:
        v = audio.tts(tts_txt or msg, spk, rate, pitch)
        add(v, st, 1.0 if spk != "arda" else 1.15)
        d = len(v) / SR
        SUB_SPANS.append((st, st + d + 0.25, msg, spk))
        voice_on[int(st * SR):int((st + d) * SR)] = 1
    # eğlenceli müzik: 104 BPM, bas + davul + akor tıngırtısı
    bpm = 104
    beat = 60 / bpm
    music = np.zeros(n, np.float32)
    chords = [(48, 52, 55), (45, 48, 52), (41, 45, 48), (43, 47, 50)]   # C Am F G
    kick = audio.sfx_step(1.0, 0.0)
    k = 0.0
    i = 0
    while k < TOTAL - 1.0:
        bar = int(i // 4) % 4
        root = chords[bar][0] - 12
        # kick 1-3, clap 2-4
        j = int(k * SR)
        if i % 2 == 0:
            seg = kick[: max(0, n - j)]
            music[j:j + len(seg)] += seg * 0.9
        else:
            m = int(0.12 * SR)
            cl = audio.bandnoise(m, 1200, 6000) * audio.env(m, 0.001, 0.03) * 0.25
            music[j:j + m] += cl[: max(0, n - j)][:m]
        # bas
        L = int(beat * 0.9 * SR)
        tt = np.arange(L) / SR
        f = 440 * 2 ** ((root - 69) / 12)
        bs = (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 2.5) * 0.35
        music[j:j + L] += bs[: max(0, n - j)][:L]
        # sekizlik akor tıngırtısı
        for half in (0, 0.5):
            jj = int((k + half * beat) * SR)
            L2 = int(0.35 * SR)
            tt2 = np.arange(L2) / SR
            pl = sum(np.sign(np.sin(2 * np.pi * 440 * 2 ** ((m_ + 12 - 69) / 12) * tt2)) for m_ in chords[bar])
            pl = pl * np.exp(-tt2 * 9) * 0.035
            music[jj:jj + L2] += pl[: max(0, n - jj)][:L2]
        k += beat
        i += 1
    duck = 1 - 0.5 * np.convolve(voice_on, np.ones(int(0.2 * SR)) / int(0.2 * SR), mode="same")
    music *= duck
    music[int(22.4 * SR):int(23.4 * SR)] *= np.linspace(1, 0.2, int(1.0 * SR))   # final öncesi nefes
    music[int(23.4 * SR):] *= 0.2 + 0.8 * np.clip((t[int(23.4 * SR):] - 25.2) / 0.5, 0, 1)
    add(music, 0, 0.9)
    # motor sesi (araba hareket ederken)
    eng = np.zeros(n, np.float32)
    a, b = int(4.3 * SR), int(13.4 * SR)
    tt = t[a:b]
    speed = np.gradient(np.array([car_x(x) for x in tt]))
    rpm = 55 + np.abs(speed) / (np.abs(speed).max() + 1e-9) * 40
    ph = np.cumsum(rpm) / SR * 2 * np.pi
    eng[a:b] = (np.sign(np.sin(ph)) * 0.4 + np.sin(2 * ph)) * 0.09 * np.minimum(1, (tt - 4.3) / 0.6)
    add(eng, 0, 1.0, 0.1)
    add(audio.sfx_whoosh(), 4.5, 1.2)
    # kapı açılış/kapanış, ayak sesleri
    add(audio.sfx_gun_cock(), 13.9, 0.6)
    add(audio.sfx_step(0.9, 0.2), 15.1, 1.0)
    k = 15.0
    while k < 22.0:
        add(audio.sfx_step(0.3, 0.25), k, 1.0)
        k += 0.46
    # final: patlama + konfeti + kalabalık tezahüratı
    add(audio.sfx_boom(), 23.35, 0.8)
    add(audio.sfx_pop(), 23.4, 1.2)
    for j, (msg, v, p) in enumerate([("Yaşa!", "hayriye", "+20Hz"), ("Hooop!", "narrator", "+10Hz"),
                                      ("Helal!", "arda", "+6Hz"), ("Yaşa be!", "hayriye", "-5Hz")]):
        add(audio.tts(msg, v, "+10%", p), 25.3 + j * 0.25, 0.45, (-0.5, 0.5, -0.2, 0.3)[j])
    peak = np.abs(out).max() + 1e-9
    return (out / peak * 0.9).T


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    args = ap.parse_args()
    out_dir = os.path.join(ROOT, "output")
    wav = os.path.join(ROOT, "build", "dassakpasa.wav")
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    mix = build_audio()
    surface = skia.Surface(W, H)
    if args.preview is not None:
        for t in args.preview:
            cv = surface.getCanvas()
            cv.clear(C("#000000"))
            frame(cv, t)
            surface.makeImageSnapshot().save(os.path.join(out_dir, f"preview_{t:05.1f}.png"), skia.kPNG)
        return
    audio.write_wav(wav, mix)
    out = os.path.join(out_dir, "dassakpasa.mp4")
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "24",
                           "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac",
                           "-b:a", "192k", "-shortest", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    n = int(TOTAL * FPS)
    for i in range(n):
        cv = surface.getCanvas()
        cv.clear(C("#000000"))
        frame(cv, i / FPS)
        ff.stdin.write(np.ascontiguousarray(surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)).tobytes())
        if i % 300 == 0:
            print(f"  kare {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("Video hazır:", out)


if __name__ == "__main__":
    main()
