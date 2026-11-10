"""Bölüm 1 senaryosu.

Her sahne: görsel sahne fonksiyonunun adı + sırayla okunan seslendirme satırları.
Satır alanları:
  text   : ekranda görünen altyazı
  tts    : seslendirmede okunan metin (yoksa text okunur, None ise sessiz)
  dur    : sessiz satırlar için süre (sn)
  style  : altyazı stili ("normal", "alert", "huh")
  sfx    : [(satır başından gecikme sn, efekt adı), ...]
Sahne alanları:
  pre / post : sahne başı / sonu boşluk (sn)
"""

SCENES = [
    dict(scene="hook", pre=0.6, post=0.5, lines=[
        dict(text="Telefonuna gelen tek bir bildirim, bütün hayatını değiştirebilir mi?",
             sfx=[(0.0, "drone_hit")]),
    ]),
    dict(scene="intro", pre=0.3, post=0.3, lines=[
        dict(text="Bu, Çorum'da yaşayan Arda Tüfeker'in hikayesi."),
        dict(text="Uzun boylu, kıvırcık kumral saçlı ve kumral sakallı bir adam."),
        dict(text="Üstünde her zamanki gibi adidas eşofman takımı var.",
             tts="Üstünde her zamanki gibi adidas eşofman takımı var."),
        dict(text="Çarşıdan sıcacık leblebisini almış, evine doğru yürüyor."),
    ]),
    dict(scene="notif", pre=0.2, post=0.4, lines=[
        dict(text="Tam o sırada telefonu titriyor.", sfx=[(0.0, "buzz"), (0.9, "ding")]),
        dict(text="Ekranda tek bir cümle yazıyor:"),
        dict(text="SAKIN SOKAĞA ÇIKMAYIN!", tts="Sakın sokağa çıkmayın!", style="alert",
             sfx=[(0.0, "sting")]),
    ]),
    dict(scene="look", pre=0.2, post=0.3, lines=[
        dict(text="Arda bir an donup kalıyor ve etrafına bakıyor."),
        dict(text="Sokakta tek bir sivil bile yok. Ne bir araba, ne bir insan."),
    ]),
    dict(scene="soldiers", pre=0.2, post=0.4, lines=[
        dict(text="Köşeye baktığında ise kalbi duracak gibi oluyor.", sfx=[(0.0, "siren")]),
        dict(text="Sokağın sonunda askerler bekliyor.", sfx=[(0.0, "boots")]),
    ]),
    dict(scene="aim", pre=0.2, post=0.5, lines=[
        dict(text="Askerlerden biri silahını yavaşça ona doğrultuyor.",
             sfx=[(1.2, "gun_cock")]),
    ]),
    dict(scene="run", pre=0.1, post=0.3, lines=[
        dict(text="Arda hiç düşünmeden eve doğru koşmaya başlıyor!", sfx=[(0.0, "whoosh")]),
        dict(text="Huh! Huh! Huh!", tts=None, dur=2.4, style="huh"),
        dict(text="Leblebiler yere saçılıyor ama arkasına bakmıyor bile."),
    ]),
    dict(scene="watch", pre=0.2, post=0.3, lines=[
        dict(text="Akıllı saati durmadan titriyor.", sfx=[(0.0, "buzz")]),
        dict(text="Nabzı tam 187'ye çıkmış!", tts="Nabzı tam yüz seksen yediye çıkmış!",
             style="alert"),
    ]),
    dict(scene="rest", pre=0.2, post=0.6, lines=[
        dict(text="Daha fazla dayanamayan Arda, bir duvarın dibinde mola veriyor."),
        dict(text="Huh... huh...", tts=None, dur=1.6, style="huh"),
    ]),
    dict(scene="girl", pre=0.3, post=1.2, lines=[
        dict(text="Tam nefesini toparlamışken, karşısında birini görüyor.",
             sfx=[(0.3, "footstep_soft"), (0.8, "footstep_soft"), (1.3, "footstep_soft")]),
        dict(text="Bu bomboş şehirde gördüğü ilk sivil...", sfx=[(0.0, "drone_hit")]),
        dict(text="Genç bir kız.", sfx=[(0.0, "sting")]),
    ]),
    dict(scene="end", pre=0.4, post=1.6, lines=[
        dict(text="Bu kız kim? Ve Çorum'da neler oluyor?", sfx=[(0.0, "boom")]),
        dict(text="İkinci bölüm için takip etmeyi unutma!"),
    ]),
]
