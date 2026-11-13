"""Rap demosu mix + mastering zinciri (stem'lerden).

Kullanım: python3 mix.py <stems klasörü> <çıkış klasörü> [hedef_LUFS]
Girdi: vocals.wav drums.wav bass.wav other.wav (aynı uzunluk, 44.1 kHz stereo)
Çıktı: master.wav (24-bit), vocal_bus.wav, beat_bus.wav, rapor yazdırır.
"""
import os
import sys

import numpy as np
import pyloudnorm as pyln
import soundfile as sf
from pedalboard import (Compressor, Gain, HighpassFilter, HighShelfFilter, Limiter, LowpassFilter, LowShelfFilter,
                        NoiseGate, PeakFilter, Pedalboard, Reverb)
from scipy.signal import butter, sosfiltfilt

STEMS, OUT = sys.argv[1], sys.argv[2]
TARGET = float(sys.argv[3]) if len(sys.argv) > 3 else -9.5
os.makedirs(OUT, exist_ok=True)
SR = 44100
BEAT = 0.627  # davul stem'inden ölçülen vuruş süresi (~95.7 BPM)
meter = pyln.Meter(SR)


def load(n):
    x, sr = sf.read(os.path.join(STEMS, n + ".wav"), dtype="float32", always_2d=True)
    assert sr == SR
    return x.T.copy()  # (2, N)


def db(x):
    return 20 * np.log10(np.maximum(x, 1e-9))


def lufs(x):
    return meter.integrated_loudness(x.T.astype(np.float64))


def env_follow(x, attack, release):
    """Basit tepe izleyici (mono, doğrusal genlik)."""
    a = np.exp(-1 / (attack * SR))
    r = np.exp(-1 / (release * SR))
    src = np.abs(x)
    out = np.empty_like(src)
    e = 0.0
    # hız için 32 örneklik bloklarla
    blk = 32
    for i in range(0, len(src), blk):
        p = src[i:i + blk].max()
        e = a * e + (1 - a) * p if p > e else r * e + (1 - r) * p
        out[i:i + blk] = e
    return out


def band(x, lo, hi):
    sos = butter(4, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfiltfilt(sos, x, axis=-1).astype(np.float32)


def hp(x, f):
    sos = butter(4, f, btype="high", fs=SR, output="sos")
    return sosfiltfilt(sos, x, axis=-1).astype(np.float32)


def lp(x, f):
    sos = butter(4, f, btype="low", fs=SR, output="sos")
    return sosfiltfilt(sos, x, axis=-1).astype(np.float32)


def dyn_band_cut(x, lo, hi, key_env, max_cut_db, thr):
    """key_env (0..1 doğrusal) eşiği geçtikçe x'in [lo,hi] bandını en fazla max_cut_db kıs."""
    b = band(x, lo, hi)
    k = np.clip((db(key_env) - thr) / 12.0, 0, 1)
    g = 10 ** (-max_cut_db * k / 20)
    return x - b + b * g


def exciter(x, lo=5500, drive=4.0, out_hp=11500, mix_db=-20):
    """Kesilmiş üst frekansları yapay harmoniklerle kısmen geri getir."""
    h = hp(x, lo)
    sat = np.tanh(h * drive / (np.abs(h).max() + 1e-9) * 3)
    sat = hp(sat, out_hp)
    sat = lp(sat, 17000)
    return x + sat * (np.sqrt(np.mean(h ** 2)) / (np.sqrt(np.mean(sat ** 2)) + 1e-9)) * 10 ** (mix_db / 20)


def deesser(x, lo=5000, hi=9500, thr_db=-30, ratio=4.0):
    s = band(x, lo, hi)
    e = env_follow(s.mean(0), 0.001, 0.05)
    over = np.maximum(db(e) - thr_db, 0)
    g = 10 ** (-(over * (1 - 1 / ratio)) / 20)
    return x - s + s * g


def delay(x, t, fb, n=4):
    d = int(t * SR)
    y = np.zeros_like(x)
    for k in range(1, n + 1):
        sh = d * k
        if sh >= x.shape[1]:
            break
        g = fb ** (k - 1)
        # ping-pong: tek yankılar sola, çiftler sağa ağırlıklı
        pan = np.array([[0.8], [0.4]]) if k % 2 else np.array([[0.4], [0.8]])
        y[:, sh:] += x.mean(0, keepdims=True)[:, :-sh] * g * pan
    return y


# ------------------------------------------------------------------ yükle
voc = load("vocals")
orig = load("orig") if os.path.exists(os.path.join(STEMS, "orig.wav")) else None
# beat = orijinal - vokal: ayırmanın kaybettiği hiçbir şey kaybolmaz
beat_raw = orig - voc
N = voc.shape[1]
rep = {}
rep["in_vocal_lufs"] = lufs(voc)

# ------------------------------------------------------------------ VOKAL
vb = Pedalboard([
    HighpassFilter(85),
    NoiseGate(threshold_db=-52, ratio=2.5, attack_ms=0.5, release_ms=250),   # hafif expander: sızıntıyı azalt
    PeakFilter(300, -4.5, 0.9),          # çamur
    PeakFilter(650, -1.0, 1.2),          # kutu sesi
    PeakFilter(3300, 1.5, 0.8),          # anlaşılırlık / varlık
    HighShelfFilter(8500, 2.0, 0.7),     # hava (12 kHz'e kadar mevcut)
])
v = vb(voc, SR)
v = deesser(v, thr_db=db(np.percentile(np.abs(band(v, 5000, 9500)), 99.7)) - 2, ratio=3.0)
comp = Pedalboard([
    Compressor(threshold_db=-24, ratio=4, attack_ms=4, release_ms=60),
    Compressor(threshold_db=-14, ratio=2.5, attack_ms=15, release_ms=140),
])
v = comp(v, SR)
# paralel saturasyon (sıcaklık)
v = v + np.tanh(v * 3.0) / 3.0 * 0.18
v = exciter(v, mix_db=-17)
v = HighpassFilter(85)(v, SR)
# vokali mono'ya yakın merkezle (ayırma kaynaklı stereo titreşimi azalt)
mid = v.mean(0, keepdims=True)
v = mid * 0.9 + v * 0.1

# ------------------------------------------------------------------ BEAT
# beat: 28 Hz altı temizle, 120 Hz altı mono, 300 Hz üstünde hafif genişlik
beat = HighpassFilter(28)(beat_raw.astype(np.float32), SR)
lo_b = lp(beat, 120)
beat = (beat - lo_b) + lo_b.mean(0, keepdims=True)
b_hi = hp(beat, 300)
b_rest = beat - b_hi
m_, s_ = b_hi.mean(0), (b_hi[0] - b_hi[1]) / 2
s_ *= 1.12
beat = b_rest + np.stack([m_ + s_, m_ - s_])
# vokal anahtarlı dinamik EQ + hafif ducking
venv = env_follow(v.mean(0), 0.005, 0.25)
vthr = db(np.percentile(venv[venv > 1e-4], 40))
beat = dyn_band_cut(beat, 1500, 5000, venv, 3.0, vthr)
duck = 10 ** (-1.5 * np.clip((db(venv) - vthr) / 12.0, 0, 1) / 20)
beat = beat * duck

# ------------------------------------------------------------------ denge
# vokal etkin bölgelerde vokal, beat'ten ~1 dB yüksek olsun (rap'te vokal önde)
active = venv > 10 ** (vthr / 20)
idx = np.where(active)[0]
seg = slice(idx[0], idx[-1]) if len(idx) else slice(0, N)
gv = (lufs(beat[:, seg]) + 0.0) - lufs(v[:, seg])
v = v * 10 ** (gv / 20)
rep["vocal_gain_db"] = gv

# ------------------------------------------------------------------ FX (gönder)
rv = Pedalboard([Reverb(room_size=0.32, damping=0.6, wet_level=1.0, dry_level=0.0, width=1.0),
                 HighpassFilter(350), LowpassFilter(7500)])(v, SR)
dl = delay(v, BEAT / 2, 0.35)                          # 1/8 nota ping-pong
dl = Pedalboard([HighpassFilter(400), LowpassFilter(5000)])(dl.astype(np.float32), SR)
fx_duck = 10 ** (-6 * np.clip((db(venv) - vthr) / 10.0, 0, 1) / 20)   # vokal konuşurken yankıyı kıs
fx = (rv * 10 ** (-17 / 20) + dl * 10 ** (-21 / 20)) * fx_duck
vocal_bus = v + fx

mix = beat + vocal_bus
sf.write(os.path.join(OUT, "vocal_bus.wav"), vocal_bus.T, SR, subtype="PCM_24")
sf.write(os.path.join(OUT, "beat_bus.wav"), beat.T, SR, subtype="PCM_24")

# ------------------------------------------------------------------ MASTER
mix = mix / (np.abs(mix).max() + 1e-9) * 0.5
mb = Pedalboard([
    HighpassFilter(26),
    LowShelfFilter(60, -1.0, 0.7),        # aşırı sub'ı biraz toparla
    PeakFilter(220, -0.8, 0.9),
    HighShelfFilter(10000, 1.0, 0.7),
    Compressor(threshold_db=-16, ratio=2.0, attack_ms=30, release_ms=200),   # glue
])
mix = mb(mix.astype(np.float32), SR)
mix = exciter(mix, lo=6000, drive=3.0, mix_db=-24)

# ton dengesi eşleştirme: tipik trap/rap master bant dağılımına (enerji payı, dB) yumuşakça yaklaş
TB = [(20, 60, -3.0), (60, 120, -4.5), (120, 250, -9.0), (250, 500, -13.0), (500, 2000, -12.5),
      (2000, 5000, -16.0), (5000, 10000, -20.0), (10000, 16000, -26.0)]


def band_shares(x):
    mm = x.mean(0)
    n = 8192
    S = np.zeros(n // 2 + 1)
    for i in range(0, len(mm) - n, n * 2):
        S += np.abs(np.fft.rfft(mm[i:i + n] * np.hanning(n))) ** 2
    f = np.fft.rfftfreq(n, 1 / SR)
    return [10 * np.log10(S[(f >= lo) & (f < hi)].sum() / S.sum()) for lo, hi, _ in TB]


for it in range(2):
    cur = band_shares(mix)
    filt = []
    for (lo, hi, tgt), c in zip(TB, cur):
        gdb = float(np.clip((tgt - c) * 0.5, -3.0, 3.0))
        fc = np.sqrt(lo * hi)
        q = fc / (hi - lo) * 1.2
        filt.append(PeakFilter(fc, gdb, max(q, 0.4)))
        rep["tb_%d_%d" % (lo, it)] = gdb
    mix = Pedalboard(filt)(mix, SR)
rep_bands = band_shares(mix)
for (lo, hi, tgt), c in zip(TB, rep_bands):
    print(f"  band {lo}-{hi}: {c:6.1f} dB (hedef {tgt})")

# hedef LUFS'a limiter ile ulaş (true-peak için 4x aşırı örnekleme)
from scipy.signal import resample_poly  # noqa: E402

def true_peak(y):
    up = resample_poly(y, 4, 1, axis=1)
    return float(db(np.abs(up).max()))


def master_at(gain_db, ceiling):
    x = (mix * 10 ** (gain_db / 20)).astype(np.float32)
    up = resample_poly(x, 4, 1, axis=1).astype(np.float32)
    up = Limiter(threshold_db=ceiling - 0.6, release_ms=90)(up, SR * 4)
    c = 10 ** (ceiling / 20)
    up = np.tanh(up / c) * c                    # 4x'te yumuşak kırpma (taşmaları yuvarla)
    return resample_poly(up, 1, 4, axis=1).astype(np.float32)


ceiling = -1.2
g = TARGET - lufs(mix)
for _ in range(8):
    y = master_at(g, ceiling)
    L, tp = lufs(y), true_peak(y)
    if tp > -1.0:
        ceiling -= (tp + 1.0) + 0.1
    g += TARGET - L
    if abs(TARGET - L) < 0.15 and tp <= -1.0:
        break
y = master_at(g, ceiling)
rep["true_peak_dbtp"] = true_peak(y)
rep["ceiling"] = ceiling
sf.write(os.path.join(OUT, "master.wav"), y.T, SR, subtype="PCM_24")
rep["master_lufs"] = lufs(y)
rep["master_peak_dbfs"] = float(db(np.abs(y).max()))
for k, val in rep.items():
    print(f"{k}: {val:.2f}")
