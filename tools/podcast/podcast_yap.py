"""Matematik I vize tekrar podcast'ini seslendirir.

Kullanım: python3 tools/podcast/podcast_yap.py [kisa]
Çıktı:    output/podcast/matematik1_vize_tekrar(.mp3|.md) ya da kısa sürüm için matematik1_vize_ozet_10dk
"""
import os
import subprocess
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio  # noqa: E402
SHORT = len(sys.argv) > 1 and sys.argv[1] == "kisa"
if SHORT:
    from matematik1_kisa import SCRIPT  # noqa: E402
else:
    from matematik1_metin import SCRIPT  # noqa: E402
BASE = "matematik1_vize_ozet_10dk" if SHORT else "matematik1_vize_tekrar"
TITLE = "Matematik I Vize — 10 Dakikalık Özet" if SHORT else "Matematik I Vize Tekrarı"

SR = audio.SR
VOICE = {"K": ("narrator", "-2%", "-2Hz"), "E": ("hayriye", "-2%", "+2Hz")}
NAMES = {"K": "Kaan", "E": "Elif"}
OUT = os.path.join(ROOT, "output", "podcast")


def chime():
    """Bölüm geçişi: iki notalı yumuşak zil."""
    n = int(1.1 * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, np.float32)
    for k, f in enumerate((784.0, 1046.5)):
        i = int(k * 0.16 * SR)
        tt = t[: n - i]
        out[i:] += (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 4.5) * 0.18
    return out


def silence(sec):
    return np.zeros(int(sec * SR), np.float32)


def main():
    os.makedirs(OUT, exist_ok=True)
    parts, md, chapters = [], [f"# {TITLE} — Podcast Dökümü", ""], []
    pos = 0.0
    total = len([s for s in SCRIPT if s[0] != "#"])
    done = 0
    for spk, txt in SCRIPT:
        if spk == "#":
            mm, ss = divmod(int(pos), 60)
            chapters.append(f"{mm:02d}:{ss:02d} {txt}")
            md += ["", f"## {txt}  ·  {mm:02d}:{ss:02d}", ""]
            seg = np.concatenate([silence(0.3), chime(), silence(0.3)])
        else:
            v, r, p = VOICE[spk]
            sig = audio.tts(txt, v, r, p).astype(np.float32)
            gap = (0.3 if SHORT else 0.45) if txt.endswith("?") else (0.25 if SHORT else 0.35)
            seg = np.concatenate([sig * 0.9, silence(gap)])
            md.append(f"**{NAMES[spk]}:** {txt}  ")
            done += 1
            if done % 20 == 0:
                print(f"  {done}/{total} satır", flush=True)
        parts.append(seg)
        pos += len(seg) / SR
    mono = np.concatenate(parts)
    wav = os.path.join(ROOT, "build", BASE + ".wav")
    os.makedirs(os.path.dirname(wav), exist_ok=True)
    audio.write_wav(wav, np.stack([mono, mono], 1))
    mp3 = os.path.join(OUT, BASE + ".mp3")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-af", "loudnorm=I=-16:TP=-1.5:LRA=7",
                    "-ac", "1", "-c:a", "libmp3lame", "-b:a", "96k",
                    "-metadata", f"title={TITLE}", "-metadata", "artist=Kaan & Elif", mp3], check=True)
    mm, ss = divmod(int(pos), 60)
    md[1:1] = ["", f"Süre: {mm} dk {ss} sn", "", "### Bölümler", ""] + [f"- {c}" for c in chapters] + [""]
    with open(os.path.join(OUT, BASE + ".md"), "w") as f:
        f.write("\n".join(md) + "\n")
    print(f"Hazır: {mp3} ({mm} dk {ss} sn)")
    print("\n".join(chapters))


if __name__ == "__main__":
    main()
