"""Bölüm 2 sahneleri — 1. bölümün karakterleri, kıyafetleri ve mekânlarıyla devam eder.

Süreklilik: Arda siyah 3 şeritli eşofman + kıvırcık kumral saç/sakal + akıllı saat;
Hayriye 1. bölümdeki gibi uzun koyu saç, bordo ceket, kot, beyaz spor ayakkabı.
Arabası: koyu gri 2023 model hatchback (Urban), plaka 35 ATF 3162.
Leblebi poşeti 1. bölümde kaçarken saçılmıştı; cepte kalan son leblebiler ikram edilir.
Saat: 1. bölümde bildirim 21:17'de geldi, 2. bölümde saat 21:30 (12'ye 2,5 saat).
"""
import math
import random

import skia

from gfx import (C, OUTLINE, SKIN, clamp, ease, ease_out_back, fill, glow, heart, hold_hands, lerp, poly,
                 pose_mix, pose_run, pose_stand, pose_walk, rrect, stroke, text, vgrad, vignette, circle)
from scenes import (ARDA, GIRL, GY, H, W, alley, camera, phone_closeup, street, watch_closeup)

GIRL_SKIN = C("#f8dcc0")


# ======================================================================= yardımcılar
def speaking(info, t, who):
    """Konuşan karakterin ağız açıklığı (dudak senkronu)."""
    for ln in info["lines"]:
        if ln["speaker"] == who and ln["a"] <= t < ln["b"]:
            u = t - ln["a"]
            return 0.25 + 0.75 * abs(math.sin(u * 13.0)) * (0.6 + 0.4 * math.sin(u * 3.1))
    return 0.0


def current(info, t):
    cur = None
    for i, ln in enumerate(info["lines"]):
        if ln["a"] - 0.15 <= t:
            cur = (i, ln)
    return cur


def floating_hearts(cv, t, n=10, seed=3, area=(0, 200, W, 1300), alpha=1.0):
    rnd = random.Random(seed)
    for i in range(n):
        x0 = rnd.uniform(area[0], area[2])
        speed = rnd.uniform(60, 140)
        ph = rnd.uniform(0, 10)
        y = area[3] - ((t * speed + ph * 100) % (area[3] - area[1]))
        x = x0 + math.sin(t * 2 + ph) * 30
        size = rnd.uniform(30, 70)
        heart(cv, x, y, size, C("#ff4d6d"), int(220 * alpha))


def name_tag(cv, t, t0, t1, name, sub, color):
    if not (t0 - 0.3 < t < t1):
        return
    k = ease(clamp((t - t0 + 0.3) / 0.4)) * clamp((t1 - t) / 0.3)
    a = int(255 * k)
    x = 60 - (1 - k) * 80
    rrect(cv, x, 240, 500, 150, 24, C("#111111", int(a * 0.75)), outline=False)
    text(cv, name, x + 30, 305, 50, skia.ColorSetA(color, a), align="left")
    text(cv, sub, x + 30, 360, 36, C("#ffffff", a), align="left")


def car(cv, x, y, s=1.0, lights=1.0):
    """Arda'nın arabası: 2023 model, koyu gri hatchback (Urban paket). Plaka 35 ATF 3162. Logo çizilmez."""
    cv.save()
    cv.translate(x, y)
    cv.scale(s, s)
    body = C("#3d4148")
    dark = C("#2a2d33")
    glass = C("#22303d")
    cv.drawOval(skia.Rect.MakeXYWH(-430, -30, 860, 60), fill(C("#000000", 110), blur=10))
    # gövde silüeti (ön sağda, arka bagaj kapağı solda eğimli)
    path = skia.Path()
    path.moveTo(-410, -40)
    path.lineTo(-420, -150)
    path.quadTo(-410, -215, -350, -250)       # eğimli arka bagaj kapağı
    path.lineTo(-250, -300)
    path.quadTo(-200, -318, -120, -320)       # tavan
    path.lineTo(80, -318)
    path.quadTo(150, -312, 210, -250)         # ön cam eğimi
    path.lineTo(300, -190)
    path.quadTo(410, -175, 425, -120)         # kaput ve burun
    path.lineTo(430, -40)
    path.close()
    cv.drawPath(path, fill(body))
    cv.drawPath(path, stroke(OUTLINE, 6))
    # camlar
    poly(cv, [(-330, -235), (-245, -285), (-150, -296), (-150, -215), (-345, -215)], glass)
    poly(cv, [(-130, -298), (40, -298), (40, -215), (-130, -215)], glass)
    poly(cv, [(60, -298), (110, -294), (185, -220), (60, -215)], glass)
    cv.drawLine(-100, -292, -125, -228, stroke(C("#ffffff", 70), 7))
    # tavan rayları (Urban)
    cv.drawLine(-260, -324, 60, -326, stroke(C("#15171b"), 10))
    # kapı çizgileri, kollar, alt marşpiyel
    cv.drawLine(-140, -215, -150, -60, stroke(dark, 4))
    cv.drawLine(50, -215, 60, -60, stroke(dark, 4))
    rrect(cv, -110, -180, 46, 10, 5, C("#8c9096"), lw=3)
    rrect(cv, 85, -180, 46, 10, 5, C("#8c9096"), lw=3)
    cv.drawLine(-380, -150, 400, -140, stroke(C("#55595f"), 3))
    rrect(cv, -400, -62, 820, 26, 10, C("#1c1e22"), lw=4)
    # LED farlar ve stoplar
    poly(cv, [(330, -175), (405, -160), (415, -138), (330, -150)], C("#e8f2ff"))
    if lights > 0:
        glow(cv, 420, -150, 320, C("#dceaff"), int(120 * lights))
    poly(cv, [(-418, -190), (-372, -200), (-372, -160), (-420, -150)], C("#d6283a"))
    glow(cv, -400, -170, 120, C("#ff2a3a"), 60)
    # plaka (35 ATF 3162)
    rrect(cv, -140, -112, 280, 46, 6, C("#ffffff"), lw=4)
    rrect(cv, -140, -112, 30, 46, 6, C("#1e4fb5"), outline=False)
    text(cv, "35 ATF 3162", 14, -77, 30, C("#111111"))
    # alaşım jantlar
    for wx in (-270, 270):
        circle(cv, wx, -30, 74, C("#1a1a1a"))
        circle(cv, wx, -30, 44, C("#9aa0a8"), lw=4)
        for k in range(5):
            ang = k * 2 * math.pi / 5
            cv.drawLine(wx, -30, wx + math.cos(ang) * 40, -30 + math.sin(ang) * 40, stroke(C("#3a3d42"), 7))
        circle(cv, wx, -30, 10, C("#3a3d42"), lw=3)
    cv.restore()


def street_two(cv, t, scroll, mood="night", lit=0.15):
    street(cv, scroll=scroll, mood=mood, lit=lit)


def hold_run_positions(ax, s, pose_a, pose_g, facing=-1):
    """El ele koşu: Arda'nın arka eli ile Hayriye'nin ön eli buluşacak şekilde Hayriye'nin x'ini bul."""
    _, _, _, arms_a, _ = ARDA.joints(pose_a)
    _, _, _, arms_g, _ = GIRL.joints(pose_g)
    hand_a = ax + s * facing * arms_a[1][2][0]
    gx = hand_a - s * facing * arms_g[0][2][0] + 40
    return gx


def run_pair(cv, t, ax, phase, expr_a="scared", expr_g="scared", gscale=0.95, **kw):
    pa = pose_run(phase)
    pg = pose_run(phase + 0.9)
    pa["arms"][1] = (-1.05 + 0.08 * math.sin(phase), 0.15)   # Arda geri uzanır
    pg["arms"][0] = (1.05 + 0.08 * math.sin(phase), 0.15)    # Hayriye ileri uzanır
    gx = hold_run_positions(ax, 1.0, pa, pg)
    GIRL.draw(cv, gx, GY, gscale, -1, pg, skin=GIRL_SKIN, look=1.0, expr=expr_g, mouth=kw.get("gmouth", 0.4))
    ARDA.draw(cv, ax, GY, 1.0, -1, pa, bag=0, expr=expr_a, look=1.0, mouth=kw.get("amouth", 0.6),
              sweat=(t * 1.5) % 1.0, t=t)
    hold_hands(cv, ARDA.hands[1], GIRL.hands[0], SKIN, GIRL_SKIN)
    return gx


def speed_lines(cv, t):
    rnd = random.Random(int(t * 12))
    for _ in range(12):
        y = rnd.uniform(200, 1700)
        x = rnd.uniform(-100, W)
        cv.drawLine(x, y, x + rnd.uniform(150, 400), y, stroke(C("#ffffff", 55), 4))


# ======================================================================= sahneler
def scene_recap(cv, t, D, info):
    z = lerp(1.0, 1.12, t / D)
    cv.save()
    camera(cv, z, W / 2, H * 0.52, t=t)
    alley(cv, t)
    ARDA.draw(cv, 330, GY, 1.0, 1, pose_stand(t * 2), bag=0, expr="surprised", look=1.0)
    GIRL.draw(cv, 820, GY, 1.0, -1, pose_stand(t * 2), skin=GIRL_SKIN, look=1.0, expr="neutral")
    text(cv, "!", 470, GY - 1130, 180, C("#ffd34d"), outline=10)
    cv.restore()
    # eski kayıt hissi: sepya + tarama çizgileri
    cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#3a2a10", 80)))
    for y in range(0, H, 6):
        cv.drawLine(0, y, W, y, stroke(C("#000000", 25), 2))
    vignette(cv, W, H, 230)
    a = int(255 * clamp(t / 0.4))
    rrect(cv, 50, 220, 560, 90, 20, C("#e53950", int(a * 0.9)), outline=False)
    poly(cv, [(110, 245), (80, 265), (110, 285)], C("#ffffff", a), outline=False)
    poly(cv, [(140, 245), (110, 265), (140, 285)], C("#ffffff", a), outline=False)
    text(cv, "ÖNCEKİ BÖLÜMDE...", 160, 282, 44, C("#ffffff", a), align="left")
    rrect(cv, W / 2 - 260, 400, 520, 190, 30, C("#000000", int(a * 0.55)), outline=False)
    text(cv, "BÖLÜM 2", W / 2, 470, 54, C("#ff4d4d", a), outline=8)
    text(cv, "HAYRİYE", W / 2, 560, 86, C("#ffffff", a), outline=10)


def scene_meet(cv, t, D, info):
    li = info["line_starts"]
    step = ease(clamp((t - 0.4) / 1.2))
    ax = lerp(300, 380, step)
    gx = 760
    cur = current(info, t)

    def target(i):
        if i is None or i < 0:
            return (W / 2, 1.0)
        return {"arda": (ax, 1.35), "hayriye": (gx, 1.35)}.get(info["lines"][i]["speaker"], (W / 2, 1.0))
    i = cur[0] if cur else None
    k = ease(clamp((t - (cur[1]["a"] if cur else 0) + 0.15) / 0.6))
    p0, p1 = target(i - 1 if i is not None else None), target(i)
    cx, z = lerp(p0[0], p1[0], k), lerp(p0[1], p1[1], k)
    cv.save()
    camera(cv, z, cx, lerp(H * 0.52, GY - 700, (z - 1) / 0.35), t=t)
    alley(cv, t)
    apose = pose_walk(t * 5, 0.5) if 0 < step < 1 else pose_stand(t * 2)
    a_expr = "smile" if t > li[1] - 0.2 else "tired"
    ARDA.draw(cv, ax, GY, 1.0, 1, apose, bag=0, expr=a_expr, look=1.0, mouth=speaking(info, t, "arda"))
    g_expr = "happy" if t > li[4] else ("surprised" if t < li[2] else "neutral")
    GIRL.draw(cv, gx, GY, 1.0, -1, pose_stand(t * 2 + 1), skin=GIRL_SKIN, look=1.0, expr=g_expr,
              mouth=speaking(info, t, "hayriye"), blush=0.3)
    cv.restore()
    vignette(cv, W, H, 170)
    name_tag(cv, t, li[2], li[4] + 2.5, "HAYRİYE", "Yozgat • köy kızı", C("#ff8fb1"))


def scene_love(cv, t, D, info):
    li = info["line_starts"]
    hold = ease(clamp((t - li[2] - 0.5) / 0.8))
    z = lerp(1.25, 1.05, ease(t / D))
    cv.save()
    camera(cv, z, W / 2 + 20, GY - 640, t=t)
    alley(cv, t)
    ax, gx = 400, 700
    pa = pose_stand(t * 2)
    pg = pose_stand(t * 2 + 1)
    pa["arms"][0] = (lerp(0.06, 0.95, hold), lerp(0.1, -0.1, hold))
    pg["arms"][0] = (lerp(0.06, 0.95, hold), lerp(0.1, -0.1, hold))
    ARDA.draw(cv, ax, GY, 1.0, 1, pa, bag=0, expr="love" if t < li[1] or t > li[2] else "smile", look=1.0,
              mouth=speaking(info, t, "arda"), blush=clamp(t / 2) * 0.8)
    blush = clamp((t - li[1]) / 1.5)
    GIRL.draw(cv, gx, GY, 1.0, -1, pg, skin=GIRL_SKIN, look=1.0,
              expr="shy" if t < li[2] else "happy", blush=blush)
    if hold > 0.9:
        hold_hands(cv, ARDA.hands[0], GIRL.hands[0], SKIN, GIRL_SKIN)
    cv.restore()
    # kalp atışı: ekran nabzı + yüzen kalpler
    beat = math.exp(-((t % 0.42) / 0.42) * 5)
    floating_hearts(cv, t, 9, alpha=0.9)
    if t < li[1]:
        heart(cv, W / 2 - 150, 520, 120 + 40 * beat, C("#ff2d55"))
    vignette(cv, W, H, 150, (80, 0, 30))


def scene_run2(cv, t, D, info):
    speed = 560
    ax = 1800 - t * speed
    scroll = ax - 430
    cv.save()
    camera(cv, 1.05, W / 2, H * 0.52, t=t, shake=4)
    street(cv, scroll=scroll, mood="night", lit=0.12)
    cv.translate(-scroll, 0)
    run_pair(cv, t, ax, t * 2 * math.pi * 1.5, expr_a="scared", expr_g="scared")
    cv.restore()
    speed_lines(cv, t)
    vignette(cv, W, H, 200)


def scene_notif2(cv, t, D, info):
    li = info["line_starts"]
    banner = clamp((t - (li[0] + 0.55)) / 0.5)
    banner2 = clamp((t - (li[0] + 0.65)) / 0.5)
    shake = 1.0 if (li[0] < t < li[0] + 1.2) else 0.0
    z = lerp(1.0, 1.08, t / D) + (0.1 * ease(clamp((t - li[1]) / 0.25)))
    cv.save()
    camera(cv, z, W / 2, 900, shake=6 * shake, t=t)
    phone_closeup(cv, t, banner, shake, clock="21:30",
                  body=("Saat 12'ye kadar tüm", "sağlıklı vatandaşlar", "havaalanlarına", "gelsin!"),
                  body_size=38, second=banner2)
    cv.restore()
    if t > li[1]:
        k = clamp((t - li[1]) / 0.2)
        cv.drawRect(skia.Rect.MakeWH(W, H), fill(C("#ff0000", int(60 * (1 - k)))))
        vignette(cv, W, H, 200, (90, 0, 0))


def scene_cry(cv, t, D, info):
    li = info["line_starts"]
    zf = ease(clamp((t - li[1] + 0.3) / 0.8))
    z = lerp(1.05, 1.55, zf)
    cx = lerp(W / 2, 400, zf)
    cy = lerp(H * 0.52, GY - 820, zf)
    cv.save()
    camera(cv, z, cx, cy, t=t, shake=1.5 * zf)
    street(cv, scroll=900, mood="night", lit=0.12)
    cv.translate(-900, 0)
    sob = math.sin(t * 9) * 4
    pa = pose_stand(t * 2)
    pa["bob"] = sob
    talk = speaking(info, t, "arda")
    ARDA.draw(cv, 1300, GY, 1.0, 1, pa, bag=0, expr="cry", look=1.0, t=t, mouth=talk)
    GIRL.draw(cv, 1660, GY, 1.0, -1, pose_stand(t * 2 + 1), skin=GIRL_SKIN, look=1.0, expr="surprised")
    cv.restore()
    vignette(cv, W, H, 190, (0, 0, 40))


def scene_watch2(cv, t, D, info):
    li = info["line_starts"]
    blink = 1.0 if t < li[1] else 0.6 + 0.4 * math.sin(t * 10)
    z = lerp(1.0, 1.15, t / D)
    cv.save()
    camera(cv, z, W / 2, 900, shake=2 if t < 0.8 else 0.8, t=t)
    watch_closeup(cv, t, 0, 0, clock="21:30", remain="12'ye 2 sa 30 dk")
    cv.restore()
    if t > li[1]:
        a = int(255 * blink)
        rrect(cv, 180, 380, 720, 110, 30, C("#e53935", a), outline=False)
        text(cv, "2,5 SAAT KALDI!", W / 2, 455, 56, C("#ffffff", a))
    vignette(cv, W, H, 220, (40, 0, 0))


def scene_plan(cv, t, D, info):
    li = info["line_starts"]
    cv.save()
    camera(cv, 1.08, W / 2, H * 0.5, t=t)
    street(cv, scroll=1400, mood="night", lit=0.15)
    cv.translate(-1400, 0)
    pg = pose_stand(t * 2 + 1)
    if li[0] - 0.1 < t < li[1]:
        pg["arms"][0] = (2.3, 0.3)   # Hayriye eliyle sokağı gösterir
    GIRL.draw(cv, 2100, GY, 1.0, -1, pg, skin=GIRL_SKIN, look=1.0, expr="neutral",
              mouth=speaking(info, t, "hayriye"))
    pa = pose_stand(t * 2)
    if t > li[1]:
        pa["arms"][0] = (1.6, 1.4)   # parmak kaldırır: "bizim araba!"
    ARDA.draw(cv, 1700, GY, 1.0, 1, pa, bag=0, expr="happy" if t > li[1] else "worried", look=1.0,
              mouth=speaking(info, t, "arda"))
    cv.restore()
    if t > li[1]:   # fikir ampulü
        k = ease_out_back(clamp((t - li[1]) / 0.35))
        cx, cy = 300 + 0, 520
        glow(cv, cx, cy, 160 * k, C("#ffe680"), 160)
        circle(cv, cx, cy, 55 * k + 1, C("#ffe680"))
        rrect(cv, cx - 22 * k, cy + 48 * k, 44 * k + 1, 30 * k + 1, 6, C("#9a9a9a"))
    if t > li[2]:   # yön tabelası
        k = ease_out_back(clamp((t - li[2]) / 0.4))
        cv.save()
        cv.translate(W - 250, 760)
        cv.scale(k, k)
        rrect(cv, -170, -60, 340, 120, 16, C("#1e6b3a"))
        text(cv, "← ARDA'NIN EVİ", 0, 18, 40, C("#ffffff"))
        cv.restore()
    vignette(cv, W, H, 180)


def scene_leblebi(cv, t, D, info):
    li = info["line_starts"]
    # koşu -> leblebi ikramında yürüyüşe yavaşla
    slow = ease(clamp((t - li[1] + 0.4) / 1.0))

    def spd(u):
        return lerp(540, 150, ease(clamp((u - li[1] + 0.4) / 1.0)))
    dt_ = 0.02
    dist = sum(spd(k * dt_) for k in range(int(t / dt_))) * dt_
    ax = 4200 - dist
    scroll = ax - 430
    cv.save()
    camera(cv, lerp(1.05, 1.3, slow), lerp(W / 2, 560, slow), lerp(H * 0.52, GY - 640, slow), t=t,
           shake=4 * (1 - slow))
    street(cv, scroll=scroll, mood="night", lit=0.2)
    cv.translate(-scroll, 0)
    if slow < 0.5:
        run_pair(cv, t, ax, t * 2 * math.pi * 1.5, expr_a="worried", expr_g="neutral")
    else:
        ph = t * 2 * math.pi * 0.9
        pa = pose_walk(ph, 0.8)
        pg = pose_walk(ph + math.pi, 0.8)
        offer = ease(clamp((t - li[1] - 0.3) / 0.6))
        eat = t > li[3] - 0.2
        pa["arms"][1] = (lerp(-0.3, -1.25, offer), lerp(0.3, -0.1, offer))   # leblebiyi uzatır
        if eat:
            pg["arms"][0] = (0.35, 2.3)   # Hayriye leblebiyi ağzına götürür
            pa["arms"][0] = (0.35, 2.3)
        else:
            pg["arms"][0] = (lerp(0.2, 1.0, offer), 0.2)
        gx = ax + 330
        chew = 0.5 + 0.5 * math.sin(t * 14)
        GIRL.draw(cv, gx, GY, 0.95, -1, pg, skin=GIRL_SKIN, look=1.0,
                  expr="chew" if eat and speaking(info, t, "hayriye") == 0 else ("happy" if eat else "shy"),
                  mouth=speaking(info, t, "hayriye") or (chew if eat else 0), blush=0.6,
                  hand_item="leblebi" if eat else None)
        ARDA.draw(cv, ax, GY, 1.0, -1, pa, bag=0, expr="chew" if eat else "smile", look=-0.6,
                  mouth=speaking(info, t, "arda") or (chew if eat else 0), hand_item="leblebi" if eat else None)
        if not eat:
            hx, hy = ARDA.hands[1]
            for i, (ox, oy) in enumerate(((-12, -14), (6, -18), (16, -6), (-4, -26), (10, -30))):
                circle(cv, hx + ox, hy + oy, 10, C("#f0d27a"), lw=3)
    cv.restore()
    if slow < 0.5:
        speed_lines(cv, t)
    else:
        floating_hearts(cv, t, 7, seed=11, alpha=slow)
    vignette(cv, W, H, 180)


def scene_end2(cv, t, D, info):
    li = info["line_starts"]
    z = lerp(1.0, 1.1, t / D)
    cv.save()
    camera(cv, z, W / 2, H * 0.55, t=t)
    street(cv, scroll=5000, mood="night", lit=0.35)
    cv.translate(-5000, 0)
    walk = ease(clamp(t / 3.0))
    ax = lerp(5000 + 560, 5000 + 350, walk)
    pa = pose_walk(t * 6, 0.6) if walk < 1 else pose_stand(t * 2)
    pg = pose_walk(t * 6 + math.pi, 0.6) if walk < 1 else pose_stand(t * 2 + 1)
    pa["arms"][1] = (-0.8, 0.1)
    pg["arms"][0] = (0.8, 0.1)
    gx = hold_run_positions(ax, 0.7, pa, pg, facing=-1)
    GIRL.draw(cv, gx, GY, 0.665, -1, pg, skin=GIRL_SKIN, look=1.0, expr="happy", blush=0.6)
    ARDA.draw(cv, ax, GY, 0.7, -1, pa, bag=0, expr="happy", look=1.0, blush=0.5)
    hold_hands(cv, ARDA.hands[1], GIRL.hands[0], SKIN, GIRL_SKIN)
    car(cv, 5600, GY + 175, 0.95, lights=0.6 + 0.4 * math.sin(t * 3))   # yolda park etmiş, önde
    cv.restore()
    floating_hearts(cv, t, 10, seed=21, area=(0, 600, W, 1500), alpha=0.8)
    vignette(cv, W, H, 200)
    k = ease_out_back(clamp((t - 0.3) / 0.6))
    rrect(cv, 40, 230, W - 80, 150, 30, C("#000000", 150), outline=False)
    text(cv, "2. BÖLÜMÜN SONU", W / 2, 335, 80 * k + 1, C("#ffffff"), outline=10)
    if len(li) > 1 and t > li[1]:
        kk = ease_out_back(clamp((t - li[1]) / 0.5))
        rrect(cv, W / 2 - 220 * kk, 420, 440 * kk + 1, 100, 50, C("#e53950"), outline=False)
        text(cv, "Takip et  +", W / 2, 488, 50 * kk + 1, C("#ffffff"))
        text(cv, "3. bölüm çok yakında...", W / 2, 580, 40, C("#ffffff", int(220 * kk)), outline=6)


SCENE_FUNCS = {
    "recap": scene_recap, "meet": scene_meet, "love": scene_love, "run2": scene_run2, "notif2": scene_notif2,
    "cry": scene_cry, "watch2": scene_watch2, "plan": scene_plan, "leblebi": scene_leblebi, "end2": scene_end2,
}
