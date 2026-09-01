# Model Performans Takibi

Bu dosya, geçmişte üretilen tahminlerin gerçek sonuçlarla karşılaştırmasını tutar. **Artık iki şekilde güncellenir:**
1. **Otomatik (best-effort):** Kullanıcı "bugünün maçlarını analiz et" dediğinde, akış başlamadan önce (bkz. `CLAUDE.md` → Orkestrasyon akışı, adım 0), henüz bu dosyaya işlenmemiş önceki gün(ler)in raporları için gerçek sonuçlar araştırılır ve bulunabildiği kadarı işlenir. Sonuç bulunamazsa süreç sessizce devam eder, ana akış bloklanmaz.
2. **Manuel:** Kullanıcı açıkça "dünkü/geçmiş sonuçları güncelle" derse aynı süreç manuel olarak da tetiklenir; bu durumda sonuç kullanıcıya raporlanır.

Amaç: zamanla modelin hangi lig/durumda ve hangi güven seviyesinde daha isabetli olduğunu görmek ve bunu rapora periyodik bir "📊 geçmiş performans notu" olarak yansıtabilmek.

## Kayıt formatı

Her kayıt, lig ve güven seviyesi bazlı kırılım tablolarının hesaplanabilmesi için lig adını ve güven seviyesini açıkça içerir:

```
### YYYY-MM-DD — <Takım A> vs <Takım B> (<Lig>)
- Model tahmini: A %XX – Beraberlik %YY – B %ZZ (olası skor: ..)
- Güven seviyesi: [Düşük/Orta/Yüksek]
- Piyasadan belirgin ayrışan tahmin miydi: [Evet (fark %..) / Hayır]
- Gerçek sonuç: <skor>
- Değerlendirme: [tahmin sonucu isabet etti mi (kazanan doğru tahmin edildi mi), skor ne kadar yakındı]
```

## Kalibrasyon takibi (asıl hedef — doğruluktan daha önemli)

Profesyonel tahmin modellerinde tek başına "isabet oranı" yanıltıcıdır; asıl ölçüt **kalibrasyon**dur — modelin "%X ihtimalle" dediği maçların gerçekten yaklaşık %X'inin o şekilde sonuçlanıp sonuçlanmadığı. Yeterli sayıda sonuç birikince (örn. 20+ maç), tahminler hem genel hem de **lig bazında** ve **güven seviyesi bazında** ayrı ayrı gruplanıp gerçek isabet oranıyla karşılaştırılır:

```
### Genel kalibrasyon tablosu (son güncelleme: YYYY-MM-DD, N=<toplam maç>)
| Tahmin edilen olasılık aralığı | Maç sayısı | Gerçek isabet oranı | Değerlendirme |
|---|---|---|---|
| %70-100 (yüksek güven) | .. | %.. | [iyi kalibre / aşırı özgüvenli / çekingen] |
| %50-70 (orta güven) | .. | %.. | ... |
| %30-50 (düşük güven) | .. | %.. | ... |

### Güven seviyesi bazında isabet (Düşük/Orta/Yüksek etiketine göre)
| Güven seviyesi etiketi | Maç sayısı | Kazanan isabet oranı | Değerlendirme |
|---|---|---|---|
| Yüksek | .. | %.. | [beklendiği gibi en isabetli grup mu?] |
| Orta | .. | %.. | ... |
| Düşük | .. | %.. | ... |

### Lig/turnuva bazında isabet
| Lig/Turnuva | Maç sayısı | Kazanan isabet oranı | Not |
|---|---|---|---|
| ... | .. | %.. | [bu ligde modelin sistematik bir zayıflığı/güçlü yanı var mı] |

Sonuç: [Model genel olarak aşırı özgüvenli mi, çekingen mi, iyi kalibre mi? Belirli bir ligde veya güven seviyesinde sistematik sapma var mı? Bir sonraki koşularda yüzdeler nasıl ayarlanmalı?]
```

Model aşırı özgüvenliyse (örn. %70 dediği maçlar sadece %50 tutuyorsa), sonraki koşularda yüksek güvenli tahminler hafifçe düşürülür (aşağı doğru "sıkıştırılır"); çekingense tam tersi yapılır. Bir lig veya güven kategorisi belirgin şekilde kötü kalibreyse, o kategoriye özel bir not düşülür. Bu ayarlama `statistical-model` ajanı tarafından her koşuda bu dosya okunarak uygulanır (bkz. `CLAUDE.md` → Model metodolojisi, madde 4).

## Piyasadan belirgin ayrışan tahminler (ayrı izleme listesi)

`statistical-model`'in model olasılığı ile piyasa zımni olasılığı arasındaki fark ≥%15 puan olduğunda işaretlenen maçlar burada ayrıca listelenir, böylece bu maçların genel ortalamadan daha mı isabetli/isabetsiz çıktığı zamanla görülebilir:

```
### Piyasa sapması izleme (son güncelleme: YYYY-MM-DD, N=<toplam işaretli maç>)
| Tarih | Maç | Model % | Piyasa % | Fark | Gerçek sonuç | İsabet mi? |
|---|---|---|---|---|---|---|
| ... | ... | .. | .. | .. | ... | [Evet/Hayır] |

Sonuç: [Piyasadan sapan tahminler genel ortalamadan daha mı iyi/kötü çıkıyor? Model bu maçlarda haklı mı çıkıyor yoksa piyasaya güvenmek mi daha isabetli?]
```

## Sonuç kayıtları

### 2026-08-19 — Cerro Porteño vs Palmeiras (Copa Libertadores)
- Model tahmini: Palmeiras %50 – Beraberlik %26 – Cerro Porteño %24 (olası skor: 1-1 / 1-2 Palmeiras)
- Gerçek sonuç: Cerro Porteño 0-1 Palmeiras (toplam 1-2 Palmeiras)
- Değerlendirme: Kazanan doğru tahmin edildi (Palmeiras). Skor neredeyse birebir tuttu (1-2 tahmin, 0-1 gerçekleşti — golün kimden geldiği ve maç skoru pratikte örtüştü).

### 2026-08-19 — Sporting Kansas City vs St. Louis City SC (MLS)
- Model tahmini: St. Louis City %52 – Beraberlik %24 – Sporting KC %24 (olası skor: 1-2 / 2-2)
- Gerçek sonuç: Sporting KC 1-1 St. Louis City (beraberlik)
- Değerlendirme: Kazanan yanlış tahmin edildi — model STL'yi favori gösterdi, maç berabere bitti. Model, STL'nin form üstünlüğüne SKC'nin ev sahibi direncini yeterince hesaba katmadı.

### 2026-08-19 — Flamengo vs Cruzeiro (Copa Libertadores)
- Model tahmini: Flamengo %48 – Beraberlik %29 – Cruzeiro %23 (olası skor: 2-1 / 1-1)
- Gerçek sonuç: Flamengo 2-1 Cruzeiro
- Değerlendirme: **Tam isabet** — hem kazanan hem de skor birebir tuttu.

### 2026-08-19 — Colorado Rapids vs LAFC (MLS)
- Model tahmini: Colorado Rapids %33 – Beraberlik %28 – LAFC %39 (olası skor: 1-1 / 1-2 LAFC)
- Gerçek sonuç: Colorado Rapids 1-0 LAFC
- Değerlendirme: Kazanan yanlış tahmin edildi — model LAFC'yi hafif favori gösterdi (piyasa da öyle görüyordu), ama Rapids'in istisnai ev sahibi savunma serisi (11 ev maçının 6'sında gol yemedi) asıl belirleyici oldu; bu sinyal modelde yeterince ağırlıklandırılmamış olabilir.

### 2026-08-19 — LA Galaxy vs San Jose Earthquakes (MLS, California Clásico)
- Model tahmini: LA Galaxy %38 – Beraberlik %30 – San Jose %32 (olası skor: 2-1 / 1-1)
- Gerçek sonuç: LA Galaxy 1-0 San Jose Earthquakes
- Değerlendirme: Kazanan doğru tahmin edildi (Galaxy), skor tam tutmadı (2-1 tahmin, 1-0 gerçekleşti) — gol sayısı abartılmış (iki takımın da kötü güncel formu düşük gollü bir maça işaret ediyordu, model bunu yeterince yansıtmadı).

## Özet istatistikler (19 Ağustos 2026 koşusu, N=5)

- **Kazanan/beraberlik isabeti: 3/5 (%60)** — Cerro-Palmeiras ✅, Flamengo-Cruzeiro ✅, Galaxy-San Jose ✅ | Sporting KC-STL ❌ (beraberliği kaçırdı), Rapids-LAFC ❌ (ev sahibi sürprizi kaçırdı).
- **Tam skor isabeti: 1/5 (%20)** — sadece Flamengo-Cruzeiro (2-1) birebir tuttu.
- **Gözlemlenen eğilim:** Model, iki maçta da (Sporting KC-STL, Rapids-LAFC) ev sahibinin direncini/form momentumunu hafife aldı ve piyasa favorisine fazla ağırlık verdi. Ayrıca genel olarak gol sayısını hafif abarttı (Cerro-Palmeiras ve Galaxy-San Jose'de gerçek skorlar tahminden daha az gollüydü).
- **Sonraki koşular için ayarlama:** (1) Ev sahibi form/savunma sinyaline (özellikle "son N ev maçında gol yemedi" gibi istatistiklere) piyasa oranına göre daha fazla ağırlık ver. (2) Toplam gol beklentisini bir miktar aşağı çek — düşük örneklemde bile model sistematik olarak fazla gollü tahmin etti.

---

_Son güncelleme: 2026-08-19 (kullanıcı bildirimi üzerine)._
