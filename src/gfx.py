"""Skia tabanlı çizim yardımcıları ve karakterler (Instagram hikaye sayfası tarzı düz 2D)."""
import math
import os

import skia

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_BOLD = skia.Typeface.MakeFromFile(os.path.join(ROOT, "assets", "fonts", "Montserrat.ttf"))
FONT_ROUND = skia.Typeface.MakeFromFile(os.path.join(ROOT, "assets", "fonts", "Nunito.ttf"))

OUTLINE = 0xFF1A1A1A
LW = 6  # çizgi kalınlığı


def C(hexstr, a=255):
    hexstr = hexstr.lstrip("#")
    r, g, b = int(hexstr[0:2], 16), int(hexstr[2:4], 16), int(hexstr[4:6], 16)
    return skia.ColorSetARGB(int(max(0, min(255, a))), r, g, b)


def shade(color, k):
    """Rengi k ile çarp (k<1 koyulaştırır)."""
    a = skia.ColorGetA(color)
    r, g, b = (min(255, int(skia.ColorGetR(color) * k)), min(255, int(skia.ColorGetG(color) * k)),
               min(255, int(skia.ColorGetB(color) * k)))
    return skia.ColorSetARGB(a, r, g, b)


def fill(color, blur=0):
    p = skia.Paint(Color=color, AntiAlias=True)
    if blur:
        p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    return p


def stroke(color, w=LW, cap=skia.Paint.kRound_Cap):
    return skia.Paint(Color=color, AntiAlias=True, Style=skia.Paint.kStroke_Style, StrokeWidth=w,
                      StrokeCap=cap, StrokeJoin=skia.Paint.kRound_Join)


def lerp(a, b, t):
    return a + (b - a) * t


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.7):
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def circle(cv, x, y, r, color, outline=True, lw=LW):
    cv.drawCircle(x, y, r, fill(color))
    if outline:
        cv.drawCircle(x, y, r, stroke(OUTLINE, lw))


def rrect(cv, x, y, w, h, r, color, outline=True, lw=LW):
    rr = skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(x, y, w, h), r, r)
    cv.drawRRect(rr, fill(color))
    if outline:
        cv.drawRRect(rr, stroke(OUTLINE, lw))


def poly(cv, pts, color, outline=True, lw=LW, closed=True):
    path = skia.Path()
    path.moveTo(*pts[0])
    for p in pts[1:]:
        path.lineTo(*p)
    if closed:
        path.close()
    cv.drawPath(path, fill(color))
    if outline:
        cv.drawPath(path, stroke(OUTLINE, lw))


def limb(cv, p, q, w, color, stripes=False, outline=True):
    """Kalın, yuvarlak uçlu uzuv. stripes=True ise eşofman üzerinde 3 beyaz şerit."""
    if outline:
        cv.drawLine(*p, *q, stroke(OUTLINE, w + LW * 2))
    cv.drawLine(*p, *q, stroke(color, w))
    if stripes:
        dx, dy = q[0] - p[0], q[1] - p[1]
        L = math.hypot(dx, dy) or 1
        ux, uy = dx / L, dy / L
        nx, ny = -uy, ux
        for k in (-1, 0, 1):
            o = k * w * 0.2
            a = (p[0] + nx * o + ux * w * 0.15, p[1] + ny * o + uy * w * 0.15)
            b = (q[0] + nx * o - ux * w * 0.15, q[1] + ny * o - uy * w * 0.15)
            cv.drawLine(*a, *b, stroke(C("#f2f2f2"), max(3, w * 0.09), skia.Paint.kButt_Cap))


def text(cv, s, x, y, size, color=0xFFFFFFFF, font=None, align="center", outline=0, outline_color=OUTLINE,
         shadow=False):
    f = skia.Font(font or FONT_BOLD, size)
    w = f.measureText(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    if shadow:
        cv.drawString(s, x + 4, y + 6, f, fill(skia.ColorSetARGB(150, 0, 0, 0), blur=6))
    if outline:
        p = stroke(outline_color, outline)
        cv.drawString(s, x, y, f, p)
    cv.drawString(s, x, y, f, fill(color))
    return w


def measure(s, size, font=None):
    return skia.Font(font or FONT_BOLD, size).measureText(s)


def wrap(s, size, maxw, font=None):
    words, lines, cur = s.split(), [], ""
    for wd in words:
        cand = (cur + " " + wd).strip()
        if measure(cand, size, font) <= maxw or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    return lines


def vgrad(cv, rect, colors, stops=None):
    x, y, w, h = rect
    sh = skia.GradientShader.MakeLinear([skia.Point(0, y), skia.Point(0, y + h)], colors, stops)
    p = skia.Paint(Shader=sh, AntiAlias=True)
    cv.drawRect(skia.Rect.MakeXYWH(x, y, w, h), p)


def glow(cv, x, y, r, color, alpha=120):
    sh = skia.GradientShader.MakeRadial(skia.Point(x, y), r,
                                        [skia.ColorSetARGB(alpha, skia.ColorGetR(color), skia.ColorGetG(color),
                                                           skia.ColorGetB(color)),
                                         skia.ColorSetARGB(0, skia.ColorGetR(color), skia.ColorGetG(color),
                                                           skia.ColorGetB(color))])
    cv.drawCircle(x, y, r, skia.Paint(Shader=sh, AntiAlias=True))


def vignette(cv, W, H, strength=200, color=(0, 0, 0)):
    sh = skia.GradientShader.MakeRadial(skia.Point(W / 2, H / 2), H * 0.75,
                                        [skia.ColorSetARGB(0, *color), skia.ColorSetARGB(int(strength), *color)],
                                        [0.45, 1.0])
    cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Shader=sh))


# ======================================================================= karakterler
SKIN = C("#f6d7b0")
SKIN_GIRL = C("#f8dcc0")


def _pt(o, ang, L):
    """o noktasından, dikeyden ang radyan (pozitif = ileri) açıyla L uzunluğunda nokta (aşağı yön)."""
    return (o[0] + math.sin(ang) * L, o[1] + math.cos(ang) * L)


def pose_walk(p, amp=1.0):
    s = math.sin(p)
    return dict(
        legs=[(0.42 * s * amp, max(0, -math.sin(p - 0.6)) * 0.7 * amp),
              (-0.42 * s * amp, max(0, math.sin(p - 0.6)) * 0.7 * amp)],
        arms=[(-0.35 * s * amp, 0.25), (0.35 * s * amp, 0.25)],
        tilt=0.03, bob=-abs(math.cos(p)) * 10 * amp)


def pose_run(p):
    s = math.sin(p)
    return dict(
        legs=[(0.85 * s, 0.3 + max(0, -math.sin(p - 0.4)) * 1.5),
              (-0.85 * s, 0.3 + max(0, math.sin(p - 0.4)) * 1.5)],
        arms=[(-0.95 * s, 1.5), (0.95 * s, 1.5)],
        tilt=0.28, bob=-abs(math.cos(p)) * 26)


def pose_stand(breath=0.0):
    return dict(legs=[(0.05, 0.0), (-0.05, 0.0)], arms=[(0.06, 0.1), (-0.06, 0.1)], tilt=0.0,
                bob=math.sin(breath) * 3)


def pose_bent(breath=0.0):
    b = math.sin(breath)
    return dict(legs=[(0.3, 0.5), (0.15, 0.4)], arms=[(-0.62 + b * 0.03, 0.05), (-0.5 + b * 0.03, 0.05)],
                tilt=0.85 + b * 0.05, bob=-25 + b * 6, head_tilt=-0.5)


def pose_mix(a, b, t):
    out = {}
    for k in ("tilt", "bob", "head_tilt"):
        out[k] = lerp(a.get(k, 0.0), b.get(k, 0.0), t)
    for k in ("legs", "arms"):
        out[k] = [(lerp(x[0], y[0], t), lerp(x[1], y[1], t)) for x, y in zip(a[k], b[k])]
    return out


class Figure:
    """Ortak iskelet: kalça merkezli ileri kinematik. Yerel koordinat: ayak tabanı (0,0), yukarı -y."""
    thigh, shin, torso, upper, fore = 215, 205, 300, 165, 150
    leg_w, arm_w, torso_w = 46, 40, 120
    head_r = 108
    pants = C("#22242a")
    jacket = C("#22242a")
    shoe = C("#f0f0f0")
    stripes = False

    def joints(self, pose):
        bob = pose.get("bob", 0)
        H = (0, -(self.thigh + self.shin) + bob + 10)
        legs = []
        for a, bend in pose["legs"]:
            k = _pt(H, a, self.thigh)
            f = _pt(k, a - bend, self.shin)
            legs.append((H, k, f))
        tilt = pose["tilt"]
        S = (H[0] + math.sin(tilt) * self.torso, H[1] - math.cos(tilt) * self.torso)
        arms = []
        for a, bend in pose["arms"]:
            e = _pt(S, a, self.upper)
            h = _pt(e, a + bend, self.fore)
            arms.append((S, e, h))
        hd = self.head_r + 18
        head = (S[0] + math.sin(tilt) * hd * 0.85, S[1] - math.cos(tilt) * hd)
        return H, S, legs, arms, head

    def draw_leg(self, cv, leg, back):
        H, k, f = leg
        col = shade(self.pants, 0.8) if back else self.pants
        limb(cv, H, k, self.leg_w, col, self.stripes)
        limb(cv, k, f, self.leg_w * 0.92, col, self.stripes)
        # ayakkabı
        rrect(cv, f[0] - 22, f[1] - 8, 76, 34, 16, shade(self.shoe, 0.85) if back else self.shoe)

    def draw_arm(self, cv, arm, back, skin):
        S, e, h = arm
        col = shade(self.jacket, 0.8) if back else self.jacket
        limb(cv, S, e, self.arm_w, col, self.stripes)
        limb(cv, e, h, self.arm_w * 0.92, col, self.stripes)
        circle(cv, h[0], h[1], 20, skin)

    def draw_torso(self, cv, H, S):
        ang = math.atan2(S[0] - H[0], -(S[1] - H[1]))
        cv.save()
        cv.translate(H[0], H[1])
        cv.rotate(math.degrees(ang))
        L = math.hypot(S[0] - H[0], S[1] - H[1])
        w = self.torso_w
        rrect(cv, -w / 2, -L - 24, w, L + 44, 40, self.jacket)
        self.torso_detail(cv, w, L)
        cv.restore()

    def torso_detail(self, cv, w, L):
        pass

    def draw(self, cv, x, y, s=1.0, facing=1, pose=None, **kw):
        pose = pose or pose_stand()
        H, S, legs, arms, head = self.joints(pose)
        cv.save()
        cv.translate(x, y)
        cv.scale(s * facing, s)
        self.draw_back(cv, head, pose, kw)
        self.draw_arm(cv, arms[1], True, kw.get("skin", SKIN))
        self.draw_leg(cv, legs[1], True)
        self.draw_leg(cv, legs[0], False)
        self.draw_torso(cv, H, S)
        self.draw_props_behind(cv, arms, kw)
        self.draw_arm(cv, arms[0], False, kw.get("skin", SKIN))
        self.draw_props_front(cv, arms, kw)
        cv.translate(head[0], head[1])
        cv.rotate(math.degrees(pose.get("head_tilt", 0.0) * 0.3))
        cv.scale(facing, 1)  # yüz her zaman düzgün okunsun
        self.draw_head(cv, facing, kw)
        cv.restore()
        return head

    def draw_back(self, cv, head, pose, kw):
        pass

    def draw_props_behind(self, cv, arms, kw):
        pass

    def draw_props_front(self, cv, arms, kw):
        pass

    def draw_head(self, cv, facing, kw):
        circle(cv, 0, 0, self.head_r, kw.get("skin", SKIN))


def draw_eyes(cv, look, expr, dx=36, y=-4):
    lx = look * 10
    if expr in ("scared", "surprised"):
        for sx in (-dx, dx):
            circle(cv, sx + lx * 0.4, y, 17, C("#ffffff"), lw=4)
            cv.drawCircle(sx + lx, y + 2, 7, fill(OUTLINE))
    elif expr == "tired":
        for sx in (-dx, dx):
            cv.drawLine(sx - 13 + lx, y + 4, sx + 13 + lx, y + 2, stroke(OUTLINE, 6))
    elif expr == "blink":
        for sx in (-dx, dx):
            cv.drawLine(sx - 11 + lx, y, sx + 11 + lx, y, stroke(OUTLINE, 6))
    else:
        for sx in (-dx, dx):
            oval = skia.Rect.MakeXYWH(sx - 9 + lx, y - 12, 18, 24)
            cv.drawOval(oval, fill(OUTLINE))
            cv.drawCircle(sx - 3 + lx, y - 6, 3.5, fill(C("#ffffff")))


def draw_mouth(cv, expr, look, y=48, color=OUTLINE, open_amt=0.0):
    lx = look * 8
    if expr in ("scared", "surprised") or open_amt > 0.05:
        h = 14 + 14 * max(open_amt, 0.6 if expr == "scared" else 0.45)
        cv.drawOval(skia.Rect.MakeXYWH(lx - 13, y - h / 2, 26, h), fill(C("#5a1f1f")))
        cv.drawOval(skia.Rect.MakeXYWH(lx - 13, y - h / 2, 26, h), stroke(color, 4))
    elif expr == "tired":
        cv.drawOval(skia.Rect.MakeXYWH(lx - 16, y - 10, 32, 22), fill(C("#5a1f1f")))
        cv.drawOval(skia.Rect.MakeXYWH(lx - 16, y - 10, 32, 22), stroke(color, 4))
    elif expr == "smile":
        path = skia.Path()
        path.moveTo(lx - 20, y - 4)
        path.quadTo(lx, y + 14, lx + 20, y - 4)
        cv.drawPath(path, stroke(color, 5))
    else:
        cv.drawLine(lx - 15, y, lx + 15, y, stroke(color, 5))


def sweat(cv, x, y, s=1.0, t=0.0):
    yy = y + (t % 1.0) * 40
    a = int(255 * (1 - (t % 1.0)))
    path = skia.Path()
    path.moveTo(x, yy - 18 * s)
    path.quadTo(x + 12 * s, yy, x, yy + 8 * s)
    path.quadTo(x - 12 * s, yy, x, yy - 18 * s)
    cv.drawPath(path, fill(C("#8fd3ff", a)))
    cv.drawPath(path, stroke(C("#1a1a1a", a), 3))


class Arda(Figure):
    """Uzun boylu, kıvırcık kumral saçlı, kumral sakallı; siyah 3 şeritli eşofman takımı."""
    thigh, shin, torso = 235, 220, 320
    pants = C("#1f2127")
    jacket = C("#1f2127")
    stripes = True
    hair = C("#9b6b3f")
    hair_dark = C("#6e4626")

    def torso_detail(self, cv, w, L):
        # fermuar ve yaka
        cv.drawLine(0, -L - 10, 0, 12, stroke(C("#d9d9d9"), 4))
        poly(cv, [(-34, -L - 22), (0, -L + 18), (34, -L - 22)], C("#2b2e35"), lw=4)

    def draw_props_front(self, cv, arms, kw):
        S, e, h = arms[0]
        if kw.get("bag", 0) > 0:
            # leblebi poşeti (kâğıt torba)
            bx, by = h[0], h[1] + 10
            cv.drawLine(h[0] - 8, h[1], bx - 22, by + 12, stroke(C("#c9a46a"), 5))
            cv.drawLine(h[0] + 8, h[1], bx + 22, by + 12, stroke(C("#c9a46a"), 5))
            rrect(cv, bx - 40, by + 10, 80, 92, 10, C("#e2c08a"))
            for i in range(5):
                circle(cv, bx - 24 + i * 12, by + 12, 9, C("#f0d27a"), lw=2)
            cv.drawLine(bx - 40, by + 34, bx + 40, by + 34, stroke(C("#b9925a"), 3))
        if kw.get("phone"):
            rrect(cv, h[0] - 16, h[1] - 50, 32, 58, 6, C("#111111"), lw=3)
            cv.drawRect(skia.Rect.MakeXYWH(h[0] - 11, h[1] - 45, 22, 46), fill(C("#7fd0ff")))
            circle(cv, h[0], h[1], 20, SKIN)
        if kw.get("watch"):
            pass

    def draw_back(self, cv, head, pose, kw):
        # kıvırcık saçın arka kısmı (başın arkası)
        hx, hy = head
        r = self.head_r
        for i in range(9):
            ang = math.radians(200 + i * 17.5)
            cv.drawCircle(hx + math.cos(ang) * (r + 6), hy + math.sin(ang) * (r + 6) * 0.95, 34,
                          fill(self.hair_dark))

    def draw_head(self, cv, facing, kw):
        r = self.head_r
        expr = kw.get("expr", "neutral")
        look = kw.get("look", 0.6)
        circle(cv, 0, 0, r, SKIN)
        # kulaklar
        circle(cv, -r + 2, 6, 18, SKIN, lw=5)
        circle(cv, r - 2, 6, 18, SKIN, lw=5)
        circle(cv, 0, 0, r, SKIN, outline=False)
        cv.drawCircle(0, 0, r, stroke(OUTLINE, LW))
        # sakal (kumral, kıvırcık kenarlı)
        beard = skia.Path()
        beard.moveTo(-r + 4, -2)
        beard.cubicTo(-r + 6, r * 0.95, r - 6, r * 0.95, r - 4, -2)
        beard.lineTo(r - 22, -2)
        beard.cubicTo(r - 30, 34, 40, 28, 0, 30)
        beard.cubicTo(-40, 28, -r + 30, 34, -r + 22, -2)
        beard.close()
        cv.drawPath(beard, fill(self.hair))
        for i in range(9):
            ang = math.radians(20 + i * 17.5)
            cv.drawCircle(math.cos(ang) * (r - 4), math.sin(ang) * (r - 4) + 4, 14, fill(self.hair))
        cv.drawPath(beard, stroke(self.hair_dark, 3))
        # bıyık
        must = skia.Path()
        must.moveTo(-34 + look * 8, 30)
        must.quadTo(look * 8, 14, 34 + look * 8, 30)
        must.quadTo(look * 8, 26, -34 + look * 8, 30)
        cv.drawPath(must, fill(self.hair_dark))
        draw_mouth(cv, expr, look, y=52, color=OUTLINE, open_amt=kw.get("mouth", 0.0))
        # baş dışını tekrar çiz
        cv.drawCircle(0, 0, r, stroke(OUTLINE, LW))
        # kaşlar
        by = -38 if expr not in ("scared", "surprised") else -52
        tilt = {"scared": 8, "worried": 8, "tired": 6, "angry": -8}.get(expr, 0)
        for sx in (-1, 1):
            cv.drawLine(sx * 22 + look * 9, by - tilt, sx * 52 + look * 9, by + tilt * 0.3,
                        stroke(self.hair_dark, 8))
        draw_eyes(cv, look, "neutral" if expr == "worried" else expr)
        # kıvırcık saç (üst)
        for i in range(13):
            ang = math.radians(185 + i * 14.2)
            rr = r + 4 + (i % 2) * 8
            x, y = math.cos(ang) * rr, math.sin(ang) * rr - 6
            circle(cv, x, y, 30 + (i % 3) * 3, self.hair, lw=4)
        for i in range(7):
            ang = math.radians(210 + i * 20)
            x, y = math.cos(ang) * (r - 26), math.sin(ang) * (r - 26) - 8
            circle(cv, x, y, 28, self.hair, lw=4)
        for i in range(6):
            x = -62 + i * 25
            circle(cv, x, -r * 0.55 + abs(i - 2.5) * 6, 22, self.hair, lw=4)
        # kıvırcık detayları
        for i in range(10):
            ang = math.radians(195 + i * 16)
            x, y = math.cos(ang) * (r - 2), math.sin(ang) * (r - 2) - 8
            p = skia.Path()
            p.addArc(skia.Rect.MakeXYWH(x - 10, y - 10, 20, 20), 200, 220)
            cv.drawPath(p, stroke(self.hair_dark, 3))
        if kw.get("sweat") is not None:
            sweat(cv, r * 0.85, -r * 0.3, 1.0, kw["sweat"])
            sweat(cv, -r * 0.9, -r * 0.1, 0.8, kw["sweat"] + 0.5)


class Soldier(Figure):
    pants = C("#55603a")
    jacket = C("#5d6a3e")
    shoe = C("#2a2420")
    torso_w = 130

    def __init__(self, seed=0):
        self.seed = seed

    def torso_detail(self, cv, w, L):
        import random
        rnd = random.Random(self.seed)
        for _ in range(9):
            x = rnd.uniform(-w / 2 + 16, w / 2 - 16)
            y = rnd.uniform(-L, 0)
            cv.drawOval(skia.Rect.MakeXYWH(x - 16, y - 10, 32, 20), fill(C("#3f4a2a")))
        rrect(cv, -w / 2 + 4, -L * 0.62, w - 8, 70, 10, C("#3c4527"), lw=4)  # yelek cebi
        cv.drawLine(-w / 2, -40, w / 2, -40, stroke(C("#2b2b20"), 12))

    def draw_leg(self, cv, leg, back):
        H, k, f = leg
        col = shade(self.pants, 0.8) if back else self.pants
        limb(cv, H, k, self.leg_w, col)
        limb(cv, k, f, self.leg_w * 0.92, col)
        rrect(cv, f[0] - 24, f[1] - 24, 80, 46, 12, self.shoe)

    def draw_props_front(self, cv, arms, kw):
        aim = kw.get("aim", 0.0)
        S = arms[0][0]
        # tüfek: aim=0 göğüste çapraz, aim=1 ileri doğrultulmuş
        ang = lerp(-0.9, 0.0, ease(aim))
        cx, cy = S[0] + lerp(-10, 40, aim), S[1] + lerp(110, 30, aim)
        cv.save()
        cv.translate(cx, cy)
        cv.rotate(math.degrees(ang))
        gun = C("#2d2f33")
        rrect(cv, -120, -16, 120, 34, 8, C("#4a3a2c"), lw=4)       # dipçik
        rrect(cv, -10, -20, 170, 34, 6, gun, lw=4)                 # gövde
        rrect(cv, 150, -12, 150, 14, 4, gun, lw=4)                 # namlu
        rrect(cv, 40, 10, 26, 56, 6, gun, lw=4)                    # şarjör
        rrect(cv, 20, -38, 60, 18, 4, gun, lw=4)                   # nişangâh
        cv.restore()

    def joints(self, pose):
        return Figure.joints(self, pose)

    def draw_head(self, cv, facing, kw):
        r = self.head_r
        circle(cv, 0, 0, r, SKIN)
        look = kw.get("look", 0.7)
        # kask
        p = skia.Path()
        p.addArc(skia.Rect.MakeXYWH(-r - 14, -r - 22, 2 * r + 28, 2 * r + 20), 180, 180)
        p.close()
        cv.drawPath(p, fill(C("#4b5530")))
        cv.drawPath(p, stroke(OUTLINE, LW))
        rrect(cv, -r - 24, -18, 2 * r + 48, 22, 10, C("#3e4727"))
        # kask kayışı
        cv.drawLine(-r + 10, 0, -r + 30, 70, stroke(C("#2b2b20"), 5))
        cv.drawLine(r - 10, 0, r - 30, 70, stroke(C("#2b2b20"), 5))
        # sert kaşlar ve gözler
        for sx in (-1, 1):
            cv.drawLine(sx * 20 + look * 9, 18 - (8 if sx > 0 else 8), sx * 52 + look * 9, 10,
                        stroke(OUTLINE, 7))
        draw_eyes(cv, look, "neutral", y=34)
        cv.drawLine(-14 + look * 8, 72, 14 + look * 8, 72, stroke(OUTLINE, 5))


class Girl(Figure):
    thigh, shin, torso = 200, 190, 280
    head_r = 100
    pants = C("#3a5f8f")
    jacket = C("#8f2d3c")
    shoe = C("#f2f2f2")
    torso_w = 110
    hair = C("#2b1d17")

    def draw_back(self, cv, head, pose, kw):
        hx, hy = head
        rrect(cv, hx - self.head_r - 14, hy - 40, 2 * self.head_r + 28, 230, 60, self.hair)

    def torso_detail(self, cv, w, L):
        cv.drawLine(0, -L - 8, 0, 10, stroke(C("#5e1c27"), 4))
        poly(cv, [(-30, -L - 20), (0, -L + 10), (30, -L - 20)], C("#e8e2d6"), lw=4)

    def draw_head(self, cv, facing, kw):
        r = self.head_r
        look = kw.get("look", -0.6)
        expr = kw.get("expr", "neutral")
        circle(cv, 0, 0, r, SKIN_GIRL)
        # perçem
        p = skia.Path()
        p.moveTo(-r - 6, 20)
        p.cubicTo(-r - 10, -r * 1.3, r + 10, -r * 1.3, r + 6, 20)
        p.cubicTo(r - 10, -30, 30, -60, -10, -40)
        p.cubicTo(-40, -30, -r + 20, -20, -r - 6, 20)
        p.close()
        cv.drawPath(p, fill(self.hair))
        cv.drawPath(p, stroke(OUTLINE, LW))
        draw_eyes(cv, look, expr, dx=34, y=8)
        # kirpik
        for sx in (-34, 34):
            cv.drawLine(sx + look * 10 + 9, -4, sx + look * 10 + 16, -10, stroke(OUTLINE, 4))
        circle(cv, -50, 40, 12, C("#f3a7a0", 160), outline=False)
        circle(cv, 50, 40, 12, C("#f3a7a0", 160), outline=False)
        draw_mouth(cv, expr if expr != "neutral" else "flat", look, y=56)
