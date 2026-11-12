"""Bölüm 2 senaryosu — "Hayriye".

Alanlar story.py ile aynı; ek olarak:
  speaker : "narrator" (varsayılan), "arda" veya "hayriye" — sesi ve altyazı etiketini belirler
"""

SCENES = [
    dict(scene="recap", pre=0.5, post=0.3, lines=[
        dict(text="Önceki bölümde Arda, bomboş Çorum sokaklarında askerlerden kaçarken bir kızla karşılaşmıştı.",
             sfx=[(0.0, "drone_hit")]),
    ]),
    dict(scene="meet", pre=0.3, post=0.4, lines=[
        dict(text="Arda nefesini toparladı ve kıza doğru bir adım attı."),
        dict(text="Biz Çorumluyuz gari! Siz nerelisiniz güzzzüm?", speaker="arda",
             tts="Biz Çorumluyuz gari! Siz nerelisiniz güzzüm?", rate="+0%"),
        dict(text="Ben Yozgatlıyım, köylü gızıyım. Adım Hayriye.", speaker="hayriye"),
        dict(text="Ne oluyo bu şehirde, heç anlamıyom!", speaker="hayriye"),
        dict(text="Hayriye, köyünden Çorum'a daha bu sabah gelmişti."),
    ]),
    dict(scene="love", pre=0.3, post=0.4, lines=[
        dict(text="Arda'nın kalbi, askerleri gördüğü andan bile hızlı atıyordu.", sfx=[(0.0, "love")]),
        dict(text="Ben seni çok sevdim. Sen beni her gece doyurursun.", speaker="arda", rate="-4%"),
        dict(text="Hayriye utançla gülümsedi ve Arda'nın elini tuttu.", sfx=[(0.6, "pop")]),
    ]),
    dict(scene="run2", pre=0.1, post=0.3, lines=[
        dict(text="El ele tutuşup yeniden koşmaya başladılar!", sfx=[(0.0, "whoosh")]),
        dict(text="Güvenli bir yer bulmaları gerekiyordu."),
    ]),
    dict(scene="notif2", pre=0.2, post=0.4, lines=[
        dict(text="Tam o sırada iki telefon da aynı anda çaldı!", sfx=[(0.0, "buzz"), (0.6, "ding2")]),
        dict(text="SAAT 12'YE KADAR TÜM SAĞLIKLI VATANDAŞLAR HAVAALANLARINA GELSİN!",
             tts="Saat on ikiye kadar tüm sağlıklı vatandaşlar havaalanlarına gelsin!", style="alert",
             sfx=[(0.0, "sting")]),
    ]),
    dict(scene="cry", pre=0.2, post=0.5, lines=[
        dict(text="Arda birden ağlamaya başladı. Hayriye'ye baktı ve...", sfx=[(0.8, "sob")]),
        dict(text="Ama Çorum'da havaalanı yok ki!", speaker="arda", rate="-12%", pitch="+20Hz",
             tts="Ama... Çorum'da havaalanı yok ki!", sfx=[(0.0, "sob")]),
    ]),
    dict(scene="watch2", pre=0.2, post=0.4, lines=[
        dict(text="Hemen akıllı saatine baktı.", sfx=[(0.0, "buzz")]),
        dict(text="Saat 12'ye sadece 2,5 saat vardı!", tts="Saat on ikiye sadece iki buçuk saat vardı!",
             style="alert", sfx=[(0.0, "drone_hit")]),
    ]),
    dict(scene="plan", pre=0.2, post=0.4, lines=[
        dict(text="Bir araba bulup gidelim!", speaker="hayriye"),
        dict(text="Bizim arabayı kullanalım!", speaker="arda", sfx=[(0.0, "pop")]),
        dict(text="Arda'nın koyu gri Egea'sı, iki sokak ötede evinin önünde duruyordu."),
    ]),
    dict(scene="leblebi", pre=0.1, post=0.4, lines=[
        dict(text="Arda'nın evine doğru koşmaya başladılar.", sfx=[(0.0, "whoosh")]),
        dict(text="Arda, eşofmanının cebinde kalan son leblebileri Hayriye'ye uzattı."),
        dict(text="Al güzzüm, Çorum leblebisi!", speaker="arda", tts="Al güzzüm, Çorum leblebisi!"),
        dict(text="Ay, pek güzelmiş gari!", speaker="hayriye", sfx=[(0.0, "crunch"), (0.5, "crunch")]),
    ]),
    dict(scene="end2", pre=0.3, post=1.6, lines=[
        dict(text="O korku dolu gecede, iki gencin aşkı da başlamış oldu.", sfx=[(0.0, "love")]),
        dict(text="Havaalanına yetişebilecekler mi? 3. bölüm için takip etmeyi unutma!",
             tts="Havaalanına yetişebilecekler mi? Üçüncü bölüm için takip etmeyi unutma!",
             sfx=[(0.0, "boom")]),
    ]),
]
