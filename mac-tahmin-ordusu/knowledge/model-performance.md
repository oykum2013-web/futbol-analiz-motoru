# Model Performans Takibi

Bu dosya, geçmişte üretilen tahminlerin gerçek sonuçlarla karşılaştırmasını tutar. Otomatik güncellenmez — kullanıcı "dünkü sonuçları güncelle" (veya benzeri) dediğinde güncellenir.

Amaç: zamanla modelin hangi lig/durumda daha isabetli olduğunu görmek ve bunu rapora "geçmiş performans notu" olarak yansıtabilmek.

## Kayıt formatı

```
### YYYY-MM-DD — <Takım A> vs <Takım B> (<Lig>)
- Model tahmini: A %XX – Beraberlik %YY – B %ZZ (olası skor: ..)
- Gerçek sonuç: <skor>
- Değerlendirme: [tahmin sonucu isabet etti mi (kazanan doğru tahmin edildi mi), skor ne kadar yakındı]
```

## Kalibrasyon takibi (asıl hedef — doğruluktan daha önemli)

Profesyonel tahmin modellerinde tek başına "isabet oranı" yanıltıcıdır; asıl ölçüt **kalibrasyon**dur — modelin "%X ihtimalle" dediği maçların gerçekten yaklaşık %X'inin o şekilde sonuçlanıp sonuçlanmadığı. Yeterli sayıda sonuç birikince (örn. 20+ maç), tahminler olasılık aralıklarına (bucket) göre gruplanıp gerçek isabet oranıyla karşılaştırılır:

```
### Kalibrasyon tablosu (son güncelleme: YYYY-MM-DD, N=<toplam maç>)
| Tahmin edilen olasılık aralığı | Maç sayısı | Gerçek isabet oranı | Değerlendirme |
|---|---|---|---|
| %70-100 (yüksek güven) | .. | %.. | [iyi kalibre / aşırı özgüvenli / çekingen] |
| %50-70 (orta güven) | .. | %.. | ... |
| %30-50 (düşük güven) | .. | %.. | ... |

Sonuç: [Model genel olarak aşırı özgüvenli mi, çekingen mi, iyi kalibre mi? Bir sonraki koşularda yüzdeler nasıl ayarlanmalı?]
```

Model aşırı özgüvenliyse (örn. %70 dediği maçlar sadece %50 tutuyorsa), sonraki koşularda yüksek güvenli tahminler hafifçe düşürülür (aşağı doğru "sıkıştırılır"); çekingense tam tersi yapılır. Bu ayarlama `statistical-model` ajanı tarafından her koşuda bu dosya okunarak uygulanır (bkz. `CLAUDE.md` → Model metodolojisi, madde 4).

## Özet istatistikler

_Henüz veri yok. İlk koşulardan sonra burada lig bazlı isabet oranı özeti tutulacak._

---

_Son güncelleme: henüz yok._
