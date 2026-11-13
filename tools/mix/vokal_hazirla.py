"""Vokal hazırlık: hafif gürültü temizleme + hafif auto-tune (Eb majör) + stereo double'lar.

Kullanım: python3 vocal_prep.py <vocals_raw.wav> <out_dir> [güç=0.55] [retune_ms=50]
Çıktı: vocals.wav (ayarlanmış, mono->stereo), doubles.wav (L/R detune double), rapor
"""
import os
import sys

import noisereduce as nr
import numpy as np
import parselmouth
import soundfile as sf
from parselmouth.praat import call

inp, out = sys.argv[1], sys.argv[2]
STRENGTH = float(sys.argv[3]) if len(sys.argv) > 3 else 0.55
RETUNE = float(sys.argv[4]) if len(sys.argv) > 4 else 50.0
SCALE = {3, 5, 7, 8, 10, 0, 2}   # Eb majör: Eb F G Ab Bb C D (perde sınıfları)
os.makedirs(out, exist_ok=True)
x, sr = sf.read(inp, dtype="float64", always_2d=True)
mono = x.mean(1)

# 1) hafif gürültü temizleme (ayırma sızıntısı / hışırtı)
clean = nr.reduce_noise(y=mono, sr=sr, stationary=False, prop_decrease=0.45, n_fft=2048,
                        time_mask_smooth_ms=64, freq_mask_smooth_hz=300)

# 2) perde analizi
snd = parselmouth.Sound(clean, sampling_frequency=sr)
manip = call(snd, "To Manipulation", 0.01, 70, 600)
ptier = call(manip, "Extract pitch tier")
n = call(ptier, "Get number of points")
times = np.array([call(ptier, "Get time from index", i + 1) for i in range(n)])
f0 = np.array([call(ptier, "Get value at index", i + 1) for i in range(n)])
midi = 69 + 12 * np.log2(f0 / 440.0)


def nearest_scale(m):
    base = np.floor(m)
    cands = [base + k for k in range(-2, 4) if int(base + k) % 12 in SCALE]
    return min(cands, key=lambda c: abs(c - m))


target = np.array([nearest_scale(m) for m in midi])
corr = (target - midi) * STRENGTH                      # yarım ton cinsinden düzeltme
# retune hızı: düzeltmeyi zamanda yumuşat (sesli bölüm sınırlarında sıfırla)
gap = np.diff(times, prepend=times[0]) > 0.03
seg_id = np.cumsum(gap)
smooth = np.zeros_like(corr)
tau = RETUNE / 1000.0
for s in np.unique(seg_id):
    idx = np.where(seg_id == s)[0]
    acc = 0.0
    for j, i in enumerate(idx):
        dt = times[i] - times[idx[j - 1]] if j else 0.01
        a = np.exp(-dt / tau)
        acc = a * acc + (1 - a) * corr[i]
        smooth[i] = acc
new_f0 = f0 * 2 ** (smooth / 12)

call(ptier, "Remove points between", 0, snd.get_total_duration())
for t, f in zip(times, new_f0):
    call(ptier, "Add point", float(t), float(f))
call([ptier, manip], "Replace pitch tier")
tuned = call(manip, "Get resynthesis (overlap-add)").values[0]
tuned = tuned[: len(mono)]
if len(tuned) < len(mono):
    tuned = np.pad(tuned, (0, len(mono) - len(tuned)))


def cents_off(fr):
    m = 69 + 12 * np.log2(fr / 440.0)
    return np.mean([abs(mm - nearest_scale(mm)) * 100 for mm in m])


print(f"perde noktası: {n}  ortalama sapma (dizi notasına): önce {cents_off(f0):.1f} cent, "
      f"sonra {cents_off(new_f0):.1f} cent")

# 3) double'lar: ±7 cent detune, 14/22 ms gecikme
def detuned(cents):
    m2 = call(snd, "To Manipulation", 0.01, 70, 600)
    pt = call(m2, "Extract pitch tier")
    call(pt, "Remove points between", 0, snd.get_total_duration())
    for t, f in zip(times, new_f0 * 2 ** (cents / 1200)):
        call(pt, "Add point", float(t), float(f))
    call([pt, m2], "Replace pitch tier")
    y = call(m2, "Get resynthesis (overlap-add)").values[0][: len(mono)]
    return np.pad(y, (0, max(0, len(mono) - len(y))))


dl = np.roll(detuned(+7), int(0.014 * sr))
dr = np.roll(detuned(-7), int(0.022 * sr))
sf.write(os.path.join(out, "vocals.wav"), np.stack([tuned, tuned], 1), sr, subtype="FLOAT")
sf.write(os.path.join(out, "doubles.wav"), np.stack([dl, dr], 1), sr, subtype="FLOAT")
print("ok")
