# Kaplan — Animasyonlu hikaye videoları

Instagram hikaye sayfalarının tarzında (düz 2D çizim, ortada büyük altyazı, seslendirme) dikey (1080x1920) animasyon videoları.

## Bölüm 1 — "Sakın Sokağa Çıkma"

Çorum'da yaşayan Arda Tüfeker (uzun boylu, kıvırcık kumral saçlı, kumral sakallı, siyah 3 şeritli eşofman takımlı) leblebisini alıp evine dönerken telefonuna "Sakın sokağa çıkmayın!" bildirimi gelir. Köşede askerleri görür, silah doğrultulunca nefes nefese kaçar, akıllı saati nabzının 187 olduğunu gösterir, mola verir... ve bir kızla karşılaşır.

Hazır video: [`output/bolum1.mp4`](output/bolum1.mp4) (~82 sn)

## Yapı

| Dosya | İçerik |
|---|---|
| `src/story.py` | Senaryo: sahneler, altyazı/seslendirme satırları, efekt zamanlamaları |
| `src/scenes.py` | Arka planlar (Çorum sokağı, saat kulesi, leblebici, ara sokak), kamera ve sahne animasyonları |
| `src/gfx.py` | Çizim yardımcıları ve karakterler (Arda, asker, kız) |
| `src/audio.py` | Piper TTS seslendirme, sentezlenmiş efektler (titreşim, siren, ayak sesi, "huh" nefesleri, kalp atışı) ve gerilim müziği |
| `src/render.py` | Zaman çizelgesini kurar, kareleri çizer, ffmpeg ile MP4 üretir |

## Yeniden üretme

```bash
pip install -r requirements.txt   # ffmpeg ve libegl1 sistemde olmalı
mkdir -p voices && cd voices
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium
curl -LO $B/tr_TR-dfki-medium.onnx && curl -LO $B/tr_TR-dfki-medium.onnx.json && cd ..
python3 src/render.py                    # -> output/bolum1.mp4
python3 src/render.py --preview 10 47    # belirli saniyelerden PNG önizleme
```

Metni değiştirmek için `src/story.py` dosyasını düzenleyip tekrar render etmek yeterli; sahne süreleri seslendirmeye göre otomatik ayarlanır.

Fontlar: Montserrat ve Nunito (SIL Open Font License).
