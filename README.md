# Hedefe-Özel Parola Adayları Üretme Aracı

## Beni Oku
Bu bölüm, script'in ne yaptığını, hangi amaçla kullanıldığını, hangi anlık bilgileri gösterdiğini ve nelere dikkat etmeniz gerektiğini kısa ve net şekilde açıklar. Lütfen okumadan çalıştırmayın.

## Amaç ve Ne Yapar
Bu Python aracı, hedefe‑özel wordlist (parola listesi) üretmek için tasarlanmıştır.  
Kullanıcıdan alınan bloklar (ör. ad, soyad, yaşadığı şehir, şehir plakası, doğum yılı, evcil hayvan ismi, tuttuğu takım vb.) temelinde tüm mantıksal kombinasyonları oluşturarak hedefe özgü parola adayları üretir.  
Amacı: büyük genel wordlist’lerde bulunamayan parolaları denemek için, sosyal mühendislikle elde edilebilecek hedefe özgü bilgilerden türetilmiş olası parola kombinasyonlarını hızlıca üretmektir.

## Çalışma Davranışı (Kısa)
Program sırasıyla şu girdileri alır: kelimeler → sayılar → özel karakterler → minimum/maksimum şifre uzunluğu → büyük/küçük harf varyant tercihi → çıktı dosyası yolu.  
Üretim, girilen blokların mantıksal dizilimleri (sıralı kombinasyonları) üzerinden ilerler ve benzersiz sonuçları dosyaya yazar.

## Anlık İzleme ve Güvenlik Mekanizması
Üretim sırasında program anlık olarak:  
- Oluşan dosyanın mevcut boyutunu (MB cinsinden)
- Üretilen satır sayısını gösterir.

Bu sayede üretim esnasında dosyanın büyümesini saniyelik bazda takip edebilirsiniz. Eğer çıktı dosyası çok büyük olacaksa (disk dolumu, sistem kaynakları üzerindeki baskı vb. riskler) bunu anında görüp işlemi durdurabilirsiniz.  
Büyük dosya oluştuğunu fark ederseniz işlemi durdurup (Ctrl+C veya process sonlandırma), girdilerinizi daraltıp tekrar deneyin.

## Kullanıcıya Kolaylık: Pozisyon ve Harf Varyantları
**Token pozisyonu kolaylığı**: Kod, girilen kelimelerin, sayıların veya özel karakterlerin "nerede" (başta/ortada/sonda) olacağını sizin manuel olarak düşünmenizi gerektirmez. Girilen blokları tüm mantıksal sıralamalarda otomatik olarak birleştirir; yani “Ömer”i başa mı sona mı koyacağınızı önceden planlamanıza gerek yok. Bu yaklaşım kullanıcıya önemli bir kolaylık sağlar — sadece hedefe ait olası token'ları girin, hangi pozisyonların denenmesi gerektiğini program halleder.

**Büyük/küçük harf varyantları**: Program size büyük/küçük harf varyantlarını genişletmek isteyip istemediğinizi sorar. "E" (evet) seçerseniz, her token için mümkün olan büyük/küçük kombinasyonları otomatik olarak üretilir ve parola adaylarına eklenir — hangi harfin büyük veya küçük olması gerektiğini bilmenize gerek kalmaz. Ancak tam kombinasyon üretimi hızla büyüyebilir; bu yüzden performans koruması amacıyla bir limit uygulanır. Eşik aşıldığında kod, anlamlı ve performans odaklı bir fallback set (ör. original, lower, upper, title) döndürür. Ayrıca üretime başlamadan önce gösterilen tahmini deneme sayısını izleyip gerekirse işlemi durdurabilirsiniz.

## Performans ve Pratik Öneriler
Girdi setiniz genişse veya min/max uzunluk kombinasyonları büyükse çıktı çok hızla büyüyebilir. İlk çalıştırmada önce küçük örneklerle (az sayıda token, dar uzunluk aralığı) test edin ve programın verdiği tahmini değerleri kontrol edin.

## Yasal ve Etik Uyarı (Kesin)
Bu araç yalnızca:
- Sahip olduğunuz sistemler ve hesaplar üzerinde,
- Veya yazılı olarak izinli olduğunuz hedeflerde kullanılmalıdır.  
İzinsiz parola denemeleri, başkalarının hesaplarına erişim teşebbüsleri veya ağlara yönelik saldırılar yasa dışıdır ve cezai sonuç doğurur. Bu kodu yalnızca eğitim, yetkilendirilmiş penetrasyon testleri ve güvenlik araştırmaları için kullanın.

## Son Notlar
Program, hedef odaklı parola tahminleri üretmek üzere güçlü ve esnek bir araçtır; ancak sorumluluğun kullanıcıda olduğunu unutmayın.  
İlk denenme aşamasında küçük parametrelerle doğrulama yapın; anlık MB ve satır sayısı göstergesi size büyümeyi kontrol etme olanağı sağlar.

Daha fazla detay ve örnek kullanım için [Medium yazımını okuyun](https://medium.com/@OmerFarukt7/hedefe-%C3%B6zel-wordlist-%C3%BCretimi-sosyal-m%C3%BChendislik-tabanl%C4%B1-parola-testleri-d449c108b316).
