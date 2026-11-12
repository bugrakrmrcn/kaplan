# Kaplan — Animasyonlu hikaye videoları

Instagram hikaye sayfalarının tarzında (düz 2D çizim, ortada büyük altyazı, seslendirme) dikey (1080x1920) animasyon videoları.

## Bölüm 1 — "Sakın Sokağa Çıkma"

Çorum'da yaşayan Arda Tüfeker (uzun boylu, kıvırcık kumral saçlı, kumral sakallı, siyah 3 şeritli eşofman takımlı) leblebisini alıp evine dönerken telefonuna "Sakın sokağa çıkmayın!" bildirimi gelir. Köşede askerleri görür, silah doğrultulunca nefes nefese kaçar, akıllı saati nabzının 187 olduğunu gösterir, mola verir... ve bir kızla karşılaşır.

Hazır video: [`output/bolum1.mp4`](output/bolum1.mp4) (~82 sn)

## Bölüm 2 — "Hayriye"

Arda, karşılaştığı Yozgatlı köy kızı Hayriye ile tanışır ("Biz Çorumluyuz gari, siz nerelisiniz güzzzüm?"), ona açılır ve el ele koşmaya başlarlar. İki telefona aynı anda "Saat 12'ye kadar tüm sağlıklı vatandaşlar havaalanlarına gelsin!" bildirimi gelir; Arda "Çorum'da havaalanı yok ki!" diye ağlar. Akıllı saatte 12'ye 2,5 saat kaldığı görülür; Arda'nın koyu gri hatchback'ine (35 ATF 3162) gitmek için koşarken cebinde kalan son leblebileri Hayriye'yle paylaşır.

Hazır video: [`output/bolum2.mp4`](output/bolum2.mp4) (~90 sn). Diyaloglarda üç ayrı ses var (anlatıcı, Arda, Hayriye); konuşanın adı altyazının üstünde görünür.

Süreklilik notları: kıyafetler, saç/sakal, akıllı saat, sokak/ara sokak 1. bölümle aynı; 1. bölümde poşet saçıldığı için leblebi eşofman cebinden çıkar; 1. bölümdeki bildirim 21:17, 2. bölümde saat 21:30.

## Yapı

| Dosya | İçerik |
|---|---|
| `src/story.py`, `src/story2.py` | Senaryolar: sahneler, altyazı/seslendirme satırları, konuşmacılar, efekt zamanlamaları |
| `src/scenes.py` | Arka planlar (Çorum sokağı, saat kulesi, leblebici, ara sokak), telefon/saat yakın planları, 1. bölüm sahneleri |
| `src/scenes2.py` | 2. bölüm sahneleri, Arda'nın arabası, el ele koşu, dudak senkronu |
| `src/gfx.py` | Çizim yardımcıları ve karakterler (Arda, asker, kız) |
| `src/audio.py` | Piper TTS seslendirme (Arda/Hayriye sesleri Praat ile türetilir), sentezlenmiş efektler (titreşim, siren, ayak sesi, "huh" nefesleri, kalp atışı) ve gerilim müziği |
| `src/render.py` | Zaman çizelgesini kurar, kareleri çizer, ffmpeg ile MP4 üretir |

## Yeniden üretme

```bash
pip install -r requirements.txt   # ffmpeg ve libegl1 sistemde olmalı
mkdir -p voices && cd voices
B=https://huggingface.co/rhasspy/piper-voices/resolve/main/tr/tr_TR/dfki/medium
curl -LO $B/tr_TR-dfki-medium.onnx && curl -LO $B/tr_TR-dfki-medium.onnx.json && cd ..
python3 src/render.py                    # -> output/bolum1.mp4
python3 src/render.py -e 2               # -> output/bolum2.mp4
python3 src/render.py -e 2 --preview 10 47   # belirli saniyelerden PNG önizleme
```

Metni değiştirmek için `src/story.py` dosyasını düzenleyip tekrar render etmek yeterli; sahne süreleri seslendirmeye göre otomatik ayarlanır.

Fontlar: Montserrat ve Nunito (SIL Open Font License).
