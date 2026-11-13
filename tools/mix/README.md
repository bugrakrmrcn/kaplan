# Rap demosu mix + mastering

1. `ayir.py <demucs_ft_klasörü> <şarkı.wav> <stems/>` — Demucs htdemucs_ft ile vokal/davul/bas/diğer
   ayırır (ağırlıklar `weights_only=True` ile, kod çalıştırmadan yüklenir).
2. Orijinal dosyayı `stems/orig.wav`, ayrılmış vokali `stems/vocals_raw.wav` olarak kopyala.
   `vokal_hazirla.py stems/vocals_raw.wav stems/ [0.7] [35]` — hafif gürültü temizleme, hafif auto-tune
   (Eb majör, güç 0.7, 35 ms retune) ve ±7 cent detune'lu stereo double'lar → `vocals.wav`, `doubles.wav`.
3. `mix_master.py <stems/> <çıkış/> [-9.5]` — vokal zinciri (expander, EQ, de-esser, 2 kademeli
   kompresör, paralel saturasyon, exciter, dinamik sertlik EQ'su, double'lar, 25 ms ön gecikmeli plate reverb + 1/8 ping-pong delay), beat = orijinal − vokal
   (vokal anahtarlı dinamik EQ, ducking, 120 Hz altı mono), master (glue, ton dengesi eşleştirme,
   4x aşırı örneklemeli limiter, true-peak ≤ -1 dBTP, hedef LUFS).

Gereken paketler: `torch demucs pedalboard pyloudnorm scipy soundfile librosa noisereduce praat-parselmouth`.
