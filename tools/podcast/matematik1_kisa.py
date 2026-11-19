"""Matematik I vize — 10 dakikalık hızlı özet (temeli bilen için)."""

SCRIPT = [
    ("#", "Giriş"),
    ("K", "Matematik Bir vize özeti. On dakikada tanım kümesinden asimptotlara kadar her şeyi kurallarıyla geçiyoruz, vize sorularını da hızlıca çözüyoruz."),

    ("#", "Tanım kümesi"),
    ("K", "Dört kural. Payda sıfır olamaz. Çift kökün içi büyük eşit sıfır. El en'in içi kesinlikle sıfırdan büyük. Kök paydadaysa içi kesinlikle pozitif. Tanjantta kosinüs sıfır olamaz, arksinüs ve arkkosinüsün içi eksi bir ile bir arasında. Birden çok parça varsa kesişim alınır."),
    ("E", "Soru bir a: karekök x eksi iki artı karekök dört eksi x."),
    ("K", "x büyük eşit iki ve x küçük eşit dört. Cevap kapalı aralık iki, dört."),
    ("E", "Bir b: el en, dört eksi üç x eksi x kare."),
    ("K", "İçi pozitif olmalı. Eksiyle çarp: x kare artı üç x eksi dört küçüktür sıfır, yani x artı dört çarpı x eksi bir küçüktür sıfır. Kökler arası: açık aralık eksi dört, bir. Logaritmada uçlar dahil değil. Kural: başkatsayının işareti köklerin dışında, tersi köklerin arasında."),

    ("#", "Limit ve süreklilik"),
    ("K", "Limitte önce yerine koy. Sayı çıkıyorsa cevap o. Sıfır bölü sıfır çıkarsa çarpanlara ayır, kök varsa eşlenikle çarp, trigonometride sinüs x bölü x'in sıfırda bir olduğunu kullan."),
    ("K", "Sayı bölü sıfır gelirse sonsuz çıkar; işareti için sağdan ve soldan ayrı bak. Limitin var olması için sağdan ve soldan limitler eşit olmalı."),
    ("K", "Sonsuzda rasyonel fonksiyonlar: payın derecesi küçükse sıfır, dereceler eşitse baş katsayılar oranı, payın derecesi büyükse sonsuz."),
    ("K", "Üstel fonksiyonlar: iki üzeri artı sonsuz, sonsuz; iki üzeri eksi sonsuz, sıfır. Kosinüs pi bölü ikide sıfır. Soldan yaklaşınca pozitif, sağdan yaklaşınca negatif. Bu yüzden bir bölü kosinüs x soldan artı sonsuza, sağdan eksi sonsuza gider."),
    ("E", "Soru iki: f x eşittir bir bölü, üç artı iki üzeri bir bölü kosinüs x. Pi bölü ikide f sıfır."),
    ("K", "Soldan: üs artı sonsuz, iki üzeri sonsuz, payda sonsuz, limit sıfır. Sağdan: üs eksi sonsuz, iki üzeri eksi sonsuz sıfır, payda üç, limit üçte bir. Sıfır ile üçte bir farklı, limit yok."),
    ("K", "Süreklilik için üç şart: f a tanımlı, limit var, limit f a'ya eşit. Limit olmadığı için pi bölü ikide sıçrama süreksizliği var. f, sıfır pi aralığında sürekli değil; diğer bütün noktalarda sürekli."),
    ("K", "Süreksizlik türleri: kaldırılabilir, sıçrama ve sonsuz. Parçalı fonksiyonu sürekli yapacak sabit sorulursa sağ limit, sol limit ve fonksiyon değerini eşitlersin. Ara değer teoremi: kapalı aralıkta sürekli fonksiyon uç değerleri arasındaki her değeri alır."),

    ("#", "Türev"),
    ("K", "Kurallar: çarpım, birincinin türevi çarpı ikinci artı birinci çarpı ikincinin türevi. Bölüm, payın türevi çarpı payda eksi pay çarpı paydanın türevi, bölü payda kare. Zincir, dıştakinin türevi çarpı içerinin türevi."),
    ("K", "Ezberler: sinüsün türevi kosinüs, kosinüsün türevi eksi sinüs, tanjantın türevi bir artı tanjant kare. E üzeri x'in türevi kendisi, a üzeri x'in türevi a üzeri x çarpı el en a. El en u'nun türevi, u türevi bölü u. Arktanjant u'nun türevi, u türevi bölü bir artı u kare. Arksinüs u'nun türevi, u türevi bölü karekök bir eksi u kare."),
    ("E", "Soru üç: y eşittir x çarpı arktanjant x bölü iki, eksi el en x kare artı dört."),
    ("K", "Çarpım kuralı: arktanjant x bölü iki, artı x çarpı yarım bölü bir artı x kare bölü dört. O terim düzenlenince iki x bölü x kare artı dört. El en'in türevi de iki x bölü x kare artı dört, önünde eksiyle. İkisi götürür. Cevap: arktanjant x bölü iki."),
    ("K", "Kapalı türevde y'li her terim zincirden y üssü alır. x üzeri x gibi ifadelerde iki tarafın el en'ini alıp türev alırsın."),

    ("#", "Artan-azalan, ekstremum ve asimptot"),
    ("K", "Türev pozitifse artan, negatifse azalan. Kritik nokta: türev sıfır ya da tanımsız. Türevi çarpanlara ayır, işaret tablosu yap. Artıdan eksiye yerel maksimum, eksiden artıya yerel minimum. İkinci türev pozitifse minimum, negatifse maksimum. Kapalı aralıkta mutlak ekstremum için kritik noktalar ve uç noktalar karşılaştırılır."),
    ("E", "Soru dört: x üzeri dört eksi sekiz x kare artı bir."),
    ("K", "Türev dört x çarpı x eksi iki çarpı x artı iki. Kritik noktalar eksi iki, sıfır ve iki. İşaretler eksi, artı, eksi, artı. Artan: eksi iki ile sıfır ve iki ile sonsuz arası. Azalan: eksi sonsuz ile eksi iki ve sıfır ile iki arası."),
    ("K", "Yerel maksimum x sıfırda, değeri bir. Yerel minimum x eksi iki ve iki'de, değeri on altı eksi otuz iki artı bir, eksi on beş. Değer sorulduğunda x'i değil, f x'i yaz."),
    ("K", "Asimptotlar. Düşey: payda sıfır olup pay sıfır olmuyorsa x eşittir a. Pay da sıfırsa önce sadeleştir; sadeleşen çarpan asimptot değil, deliktir. El en x'in x eşittir sıfırda, tanjantın pi bölü iki artı k pi'de düşey asimptotu var."),
    ("K", "Yatay: x artı ve eksi sonsuza giderken limit sayıysa y eşittir o sayı; dereceler kuralı burada da geçerli. E üzeri x'in eksi sonsuzda y eşittir sıfır, arktanjantın artı ve eksi pi bölü iki yatay asimptotları var."),
    ("K", "Eğik: payın derecesi paydanınkinden bir fazlaysa polinom bölmesi yap, bölüm y eşittir m x artı n eğik asimptot. Genel yol: m, f x bölü x'in sonsuzdaki limiti; n, f x eksi m x'in limiti. Örnek: x kare artı bir bölü x eksi bir'de eğik asimptot y eşittir x artı bir, düşey asimptot x eşittir bir."),

    ("#", "Son tekrar"),
    ("E", "Son otuz saniye."),
    ("K", "Tanım kümesinde kesişim ve uçlara dikkat. Limitte önce yerine koy, şüpheli noktada sağdan ve soldan bak. Süreklilikte üç şart. Türevde zincir kuralını unutma. Ekstremumda işaret tablosu ve f x değeri. Asimptotta sadeleştirmeyi unutma. Her cevabın sonuna kısa bir gerekçe cümlesi yaz. Başarılar!"),
]
