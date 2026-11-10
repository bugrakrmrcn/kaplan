"""Seslendirme (Piper TTS), ses efektleri ve arka plan müziği — hepsi çevrimdışı üretilir."""
import hashlib
import os
import subprocess
import sys
import wave

import numpy as np

SR = 44100
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(ROOT, "build", "tts")
VOICE = os.environ.get("PIPER_VOICE", os.path.join(ROOT, "voices", "tr_TR-dfki-medium.onnx"))
LENGTH_SCALE = 0.92
rng = np.random.default_rng(7)


# ---------------------------------------------------------------- yardımcılar
def read_wav(path):
    with wave.open(path) as w:
        sr, n, ch = w.getframerate(), w.getnframes(), w.getnchannels()
        data = np.frombuffer(w.readframes(n), dtype=np.int16).astype(np.float32) / 32768
    if ch > 1:
        data = data.reshape(-1, ch).mean(axis=1)
    if sr != SR:
        x_old = np.linspace(0, 1, len(data), endpoint=False)
        x_new = np.linspace(0, 1, int(len(data) * SR / sr), endpoint=False)
        data = np.interp(x_new, x_old, data).astype(np.float32)
    return data


def write_wav(path, stereo):
    stereo = np.clip(stereo, -1, 1)
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((stereo * 32767).astype(np.int16).tobytes())


def trim(x, thr=0.01):
    idx = np.where(np.abs(x) > thr)[0]
    if len(idx) == 0:
        return x
    return x[max(0, idx[0] - 400): idx[-1] + 2000]


def tts(text):
    """Metni seslendirir, önbellekler ve float32 mono dizi döndürür."""
    os.makedirs(CACHE, exist_ok=True)
    key = hashlib.md5(f"{text}|{LENGTH_SCALE}".encode()).hexdigest()[:12]
    path = os.path.join(CACHE, key + ".wav")
    if not os.path.exists(path):
        subprocess.run([sys.executable, "-m", "piper", "-m", VOICE, "-f", path,
                        "--length-scale", str(LENGTH_SCALE), "--noise-scale", "0.6"],
                       input=text.encode(), check=True, capture_output=True)
    v = trim(read_wav(path))
    v = v / (np.abs(v).max() + 1e-6) * 0.9
    return v


def env(n, attack, decay):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def bandnoise(n, lo, hi):
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1 / SR)
    spec[(f < lo) | (f > hi)] = 0
    x = np.fft.irfft(spec, n)
    return (x / (np.abs(x).max() + 1e-6)).astype(np.float32)


def sine(freq, dur, phase=0):
    t = np.arange(int(dur * SR)) / SR
    return np.sin(2 * np.pi * freq * t + phase).astype(np.float32)


# ---------------------------------------------------------------- efektler
def sfx_buzz():
    d = 1.0
    t = np.arange(int(d * SR)) / SR
    tone = np.sign(np.sin(2 * np.pi * 160 * t)) * 0.5 + np.sin(2 * np.pi * 80 * t)
    gate = ((t % 0.5) < 0.32).astype(np.float32)
    return (tone * gate * 0.25).astype(np.float32)


def sfx_ding():
    n = int(1.2 * SR)
    a = sine(1318.5, 1.2) * env(n, 0.005, 0.35)
    b = np.zeros(n, np.float32)
    off = int(0.12 * SR)
    b[off:] = (sine(1760, 1.2) * env(n, 0.005, 0.45))[: n - off]
    return (a + b) * 0.3


def sfx_sting():
    d = 1.8
    n = int(d * SR)
    t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * t) for f in (55, 58.3, 110, 116.5)) / 4
    x += bandnoise(n, 2000, 6000) * 0.15 * np.exp(-t * 6)
    return (x * env(n, 0.01, 0.7) * 0.6).astype(np.float32)


def sfx_drone_hit():
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 41 * t) + 0.5 * np.sin(2 * np.pi * 61.7 * t)
    x += bandnoise(n, 30, 300) * 0.6
    return (x * env(n, 0.02, 1.0) * 0.5).astype(np.float32)


def sfx_boom():
    n = int(3.0 * SR)
    t = np.arange(n) / SR
    f = 70 * np.exp(-t * 2) + 30
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) + bandnoise(n, 20, 400) * 0.5 * np.exp(-t * 3)
    return (x * env(n, 0.005, 1.2) * 0.7).astype(np.float32)


def sfx_siren():
    d = 5.0
    t = np.arange(int(d * SR)) / SR
    f = 700 + 300 * np.sin(2 * np.pi * 0.5 * t)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR)
    fade = np.minimum(1, t / 1.5) * np.minimum(1, (d - t) / 1.5)
    return (x * fade * 0.06).astype(np.float32)


def sfx_step(strength=1.0, crunch=0.3):
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * (90 * np.exp(-t * 20) + 40) * t) * np.exp(-t * 35)
    grit = bandnoise(n, 800, 4000) * np.exp(-t * 60) * crunch
    return ((thump + grit) * 0.5 * strength).astype(np.float32)


def sfx_boots():
    out = np.zeros(int(2.0 * SR), np.float32)
    for k in range(6):
        s = sfx_step(0.6, 0.6)
        i = int(k * 0.33 * SR)
        out[i:i + len(s)] += s
    return out


def sfx_footstep_soft():
    return sfx_step(0.5, 0.2)


def sfx_gun_cock():
    out = np.zeros(int(0.6 * SR), np.float32)
    for off, f_lo in ((0.0, 2500), (0.16, 1800)):
        n = int(0.05 * SR)
        c = bandnoise(n, f_lo, 9000) * env(n, 0.001, 0.012)
        i = int(off * SR)
        out[i:i + n] += c * 0.9
    return out


def sfx_whoosh():
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    x = bandnoise(n, 300, 3000) * np.sin(np.pi * t / 0.7) ** 2
    return (x * 0.3).astype(np.float32)


def sfx_huh(pitch=1.0, strength=1.0):
    """Nefes nefese "huh" sesi: nefesli gürültü + hafif sesli bileşen."""
    d = 0.32
    n = int(d * SR)
    t = np.arange(n) / SR
    breath = bandnoise(n, 400, 2600)
    f0 = 140 * pitch * (1 - 0.25 * t / d)
    voiced = np.sin(2 * np.pi * np.cumsum(f0) / SR)
    voiced = voiced + 0.5 * np.sin(2 * np.pi * np.cumsum(2 * f0) / SR) + 0.25 * np.sin(2 * np.pi * np.cumsum(3 * f0) / SR)
    e = env(n, 0.02, 0.09)
    x = (breath * 0.8 + voiced * 0.35) * e
    return (x * 0.5 * strength).astype(np.float32)


def sfx_heartbeat():
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    beat = np.sin(2 * np.pi * 55 * t) * np.exp(-t * 25)
    out = np.zeros(n, np.float32)
    out += beat
    i = int(0.16 * SR)
    out[i:] += (beat * 0.7)[: n - i]
    return out * 0.9


SFX = {
    "buzz": sfx_buzz, "ding": sfx_ding, "sting": sfx_sting, "drone_hit": sfx_drone_hit,
    "boom": sfx_boom, "siren": sfx_siren, "boots": sfx_boots, "gun_cock": sfx_gun_cock,
    "whoosh": sfx_whoosh, "footstep_soft": sfx_footstep_soft,
}


# ---------------------------------------------------------------- müzik
def music(total, scene_spans):
    """Gerilimli ambient alt yapı. Yoğunluk sahneye göre değişir."""
    n = int(total * SR)
    t = np.arange(n) / SR
    intensity = np.full(n, 0.35, np.float32)
    level = {"hook": 0.5, "intro": 0.3, "notif": 0.55, "look": 0.6, "soldiers": 0.8, "aim": 0.95,
             "run": 1.0, "watch": 0.9, "rest": 0.6, "girl": 0.7, "end": 0.5}
    for name, a, b in scene_spans:
        intensity[int(a * SR):int(b * SR)] = level.get(name, 0.4)
    # yumuşat
    k = int(0.8 * SR)
    intensity = np.convolve(intensity, np.ones(k) / k, mode="same").astype(np.float32)

    lfo = 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * t)
    pad = (np.sin(2 * np.pi * 55 * t) + 0.6 * np.sin(2 * np.pi * 82.4 * t)
           + 0.35 * np.sin(2 * np.pi * 110.3 * t) + 0.2 * np.sin(2 * np.pi * 130.8 * t)) * lfo
    pad = pad * 0.06
    # nabız gibi vuruş (yoğunlukla hızlanır)
    pulse = np.zeros(n, np.float32)
    kick = sfx_heartbeat()
    pos = 0.0
    while pos < total:
        i = int(pos * SR)
        lvl = float(intensity[min(i, n - 1)])
        if lvl > 0.45:
            seg = kick[: max(0, min(len(kick), n - i))]
            pulse[i:i + len(seg)] += seg * (lvl - 0.3) * 0.35
        pos += 1.0 / (0.9 + lvl * 1.6)
    # yüksek gerilimde tiz titreşim
    shimmer = np.sin(2 * np.pi * 880 * t) * np.sin(2 * np.pi * 6 * t) * 0.012
    return (pad * (0.5 + intensity) + pulse + shimmer * np.clip(intensity - 0.6, 0, 1) * 2).astype(np.float32)


def mix(total, voice_events, sfx_events, scene_spans, extra):
    n = int(total * SR) + SR
    L = np.zeros(n, np.float32)
    R = np.zeros(n, np.float32)

    def add(sig, at, gain=1.0, pan=0.0):
        i = int(at * SR)
        if i >= n:
            return
        sig = sig[: n - i]
        L[i:i + len(sig)] += sig * gain * (1 - max(pan, 0))
        R[i:i + len(sig)] += sig * gain * (1 + min(pan, 0))

    m = music(total, scene_spans)
    # konuşma sırasında müziği kıs (ducking)
    duck = np.ones(n, np.float32)
    for sig, at in voice_events:
        a, b = int(at * SR), int((at + len(sig) / SR) * SR)
        duck[a:b] = 0.55
    k = int(0.25 * SR)
    duck = np.convolve(duck, np.ones(k) / k, mode="same")
    mm = np.zeros(n, np.float32)
    mm[: len(m)] = m
    L += mm * duck
    R += mm * duck

    for sig, at in voice_events:
        add(sig, at, 1.0)
    for name, at in sfx_events:
        add(SFX[name](), at, 1.0)
    for sig, at, gain, pan in extra:
        add(sig, at, gain, pan)

    st = np.stack([L, R], axis=1)[: int(total * SR)]
    peak = np.abs(st).max()
    return st / max(peak, 1e-6) * 0.92
