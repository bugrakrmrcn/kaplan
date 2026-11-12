"""Bölüm videosunu üretir: seslendirme + efektler + animasyon -> output/bolum<N>.mp4

Kullanım:
  python3 src/render.py                      # 1. bölüm
  python3 src/render.py --episode 2          # 2. bölüm
  python3 src/render.py -e 2 --preview 3 12  # verilen saniyelerden PNG kareleri (output/preview_*.png)
"""
import argparse
import os
import subprocess
import sys

import numpy as np
import skia

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib  # noqa: E402

import audio  # noqa: E402
from gfx import C, clamp, ease_out_back, rrect, text, wrap  # noqa: E402
from scenes import H, W  # noqa: E402

EPISODES = {1: ("story", "scenes"), 2: ("story2", "scenes2")}
SCENES = []
SCENE_FUNCS = {}
SPEAKER_TAG = {"arda": ("ARDA", C("#ffd34d")), "hayriye": ("HAYRİYE", C("#ff8fb1"))}

FPS = 30
GAP = 0.28
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "output")
BUILD = os.path.join(ROOT, "build")


def build_timeline():
    t = 0.0
    timeline, voice, sfx, extra, subs = [], [], [], [], []
    for sc in SCENES:
        start = t
        t += sc.get("pre", 0.2)
        starts, lines = [], []
        for ln in sc["lines"]:
            starts.append(t - start)
            spoken = ln.get("tts", ln["text"])
            spk = ln.get("speaker", "narrator")
            if spoken:
                sig = audio.tts(spoken, spk)
                dur = len(sig) / audio.SR
                voice.append((sig, t))
            else:
                dur = ln.get("dur", 1.5)
            for off, name in ln.get("sfx", []):
                sfx.append((name, t + off))
            subs.append(dict(text=ln["text"], a=t, b=t + dur + GAP * 0.8, style=ln.get("style", "normal"),
                             speaker=spk))
            lines.append(dict(a=t - start, b=t - start + dur, speaker=spk))
            t += dur + GAP
        t += sc.get("post", 0.3)
        timeline.append(dict(name=sc["scene"], a=start, b=t, line_starts=starts, lines=lines))
    total = t

    # sahneye bağlı ritmik efektler
    for s in timeline:
        if s["name"] == "intro":  # yürüyüş adımları
            k = s["a"] + 0.3
            while k < s["b"]:
                extra.append((audio.sfx_step(0.35, 0.25), k, 1.0, 0.0))
                k += 1 / (0.85 * 2)
        if s["name"] in ("run2", "leblebi"):   # iki kişinin koşu adımları + nefesler
            run_end = s["b"] if s["name"] == "run2" else s["a"] + s["line_starts"][1] + 0.3
            k = s["a"]
            while k < run_end:
                extra.append((audio.sfx_step(0.7, 0.5), k, 1.0, -0.2))
                extra.append((audio.sfx_step(0.45, 0.4), k + 0.17, 1.0, 0.2))
                k += 1 / (1.5 * 2)
            k, i = s["a"] + 0.25, 0
            while k < run_end:
                extra.append((audio.sfx_huh(1.0 if i % 2 == 0 else 1.5, 0.5), k, 1.0, 0.0))
                k += 0.4
                i += 1
            if s["name"] == "leblebi":
                k = run_end + 0.2
                while k < s["b"]:
                    extra.append((audio.sfx_step(0.25, 0.2), k, 1.0, 0.0))
                    k += 1 / (0.9 * 2)
        if s["name"] == "run":
            k = s["a"]
            while k < s["b"]:
                extra.append((audio.sfx_step(0.8, 0.5), k, 1.0, 0.0))
                k += 1 / (1.6 * 2)
            k, i = s["a"] + 0.2, 0
            huh_a = s["a"] + s["line_starts"][1] - 0.2
            huh_b = s["a"] + s["line_starts"][2] + 0.4
            while k < s["b"]:
                strong = huh_a <= k <= huh_b
                if strong or i % 2 == 0:
                    extra.append((audio.sfx_huh(1.0 + 0.06 * (i % 3), 1.2 if strong else 0.55), k, 1.0, 0.0))
                k += 0.36 if strong else 0.42
                i += 1
        if s["name"] == "watch":
            k = s["a"] + 0.2
            while k < s["b"]:
                prog = clamp((k - s["a"]) / (s["b"] - s["a"]))
                extra.append((audio.sfx_heartbeat(), k, 0.9, 0.0))
                k += 60 / (96 + 91 * prog)
        if s["name"] == "rest":
            k, i = s["a"] + 0.1, 0
            while k < s["b"] + 0.8:
                extra.append((audio.sfx_huh(0.9, max(0.3, 1.0 - i * 0.05)), k, 1.0, 0.0))
                k += 0.5 + i * 0.03
                i += 1
    spans = [(s["name"], s["a"], s["b"]) for s in timeline]
    return total, timeline, voice, sfx, extra, subs, spans


def draw_subtitle(cv, sub, t):
    size = {"normal": 64, "alert": 82, "huh": 92}[sub["style"]]
    color = {"normal": C("#ffffff"), "alert": C("#ff3b3b"), "huh": C("#ffffff")}[sub["style"]]
    lines = wrap(sub["text"], size, W - 140)
    tag = SPEAKER_TAG.get(sub.get("speaker"))
    pop = ease_out_back(clamp((t - sub["a"]) / 0.18), 2.2)
    cy = 1230
    lh = size * 1.18
    y0 = cy - (len(lines) - 1) * lh / 2
    cv.save()
    cv.translate(W / 2, cy)
    s = 0.85 + 0.15 * pop
    cv.scale(s, s)
    cv.translate(-W / 2, -cy)
    if tag:
        name, col = tag
        ty = y0 - size * 0.95
        rrect(cv, W / 2 - 120, ty - 44, 240, 58, 29, col, outline=False)
        text(cv, name, W / 2, ty - 2, 38, C("#1a1a1a"))
    for i, ln in enumerate(lines):
        text(cv, ln, W / 2, y0 + i * lh + size * 0.35, size, color, outline=size * 0.2,
             outline_color=C("#151515"), shadow=True)
    cv.restore()


def render_frame(surface, t, timeline, subs):
    cv = surface.getCanvas()
    cv.clear(C("#000000"))
    scene = next((s for s in timeline if s["a"] <= t < s["b"]), timeline[-1])
    lt = t - scene["a"]
    D = scene["b"] - scene["a"]
    cv.save()
    SCENE_FUNCS[scene["name"]](cv, lt, D, scene)
    cv.restore()
    # sahne geçişi: kısa kararma
    fade = max(clamp(1 - lt / 0.18), clamp(1 - (D - lt) / 0.12))
    if scene is timeline[-1]:
        fade = max(clamp(1 - lt / 0.18), clamp(1 - (D - lt) / 0.6))
    if fade > 0:
        cv.drawRect(skia.Rect.MakeWH(W, H), skia.Paint(Color=skia.ColorSetARGB(int(255 * fade), 0, 0, 0)))
    for sub in subs:
        if sub["a"] <= t < sub["b"]:
            draw_subtitle(cv, sub, t)
    # ilerleme çubuğu (reels hissi)
    return cv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--preview", nargs="*", type=float)
    ap.add_argument("-e", "--episode", type=int, default=1, choices=sorted(EPISODES))
    args = ap.parse_args()
    story_mod, scenes_mod = EPISODES[args.episode]
    SCENES[:] = importlib.import_module(story_mod).SCENES
    SCENE_FUNCS.update(importlib.import_module(scenes_mod).SCENE_FUNCS)
    ep = args.episode
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(BUILD, exist_ok=True)

    total, timeline, voice, sfx, extra, subs, spans = build_timeline()
    print(f"Toplam süre: {total:.1f} sn")
    for s in timeline:
        print(f"  {s['name']:9s} {s['a']:6.2f} - {s['b']:6.2f}")

    surface = skia.Surface(W, H)
    if args.preview is not None:
        for t in args.preview:
            render_frame(surface, t, timeline, subs)
            surface.makeImageSnapshot().save(os.path.join(OUT, f"preview_{t:05.1f}.png"), skia.kPNG)
        return

    wav = os.path.join(BUILD, f"bolum{ep}.wav")
    audio.write_wav(wav, audio.mix(total, voice, sfx, spans, extra))
    print("Ses hazır:", wav)

    out = os.path.join(OUT, f"bolum{ep}.mp4")
    ff = subprocess.Popen([
        "ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{W}x{H}",
        "-r", str(FPS), "-i", "-", "-i", wav, "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out,
    ], stdin=subprocess.PIPE)
    n = int(total * FPS)
    for i in range(n):
        render_frame(surface, i / FPS, timeline, subs)
        arr = surface.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)
        ff.stdin.write(np.ascontiguousarray(arr).tobytes())
        if i % 150 == 0:
            print(f"  kare {i}/{n}", flush=True)
    ff.stdin.close()
    ff.wait()
    print("Video hazır:", out)


if __name__ == "__main__":
    main()
