# Maç Tahmin Ordusu — CLAUDE.md

Bu dosya `mac-tahmin-ordusu/` klasörü altında çalışırken geçerlidir ve tüm ajanları bağlar. Buradaki kurallar diğer tüm talimatlardan üstündür.

Bu proje, ana repodaki `ajan_ordusu/` (Python prototipi) ve `agent-ordusu/` (Etsy ordusu, bu repoda yok) klasörlerinden **tamamen bağımsızdır**. Hiçbir dosya, ajan veya bilgi bankası paylaşılmaz.

Tam tasarım dokümanı: [`mac-tahmin-ordusu-master-prompt.md`](./mac-tahmin-ordusu-master-prompt.md).

## Amaç

Kullanıcı "bugünün maçlarını analiz et" (veya benzeri) dediğinde, o gün oynanacak tüm liglerdeki tüm maçları tek tek analiz edip tek bir raporda (`reports/YYYY-MM-DD-mac-analizleri.md`) alt alta sunmak. Her maç için: form, h2h, kadro/sakatlık/ceza (yedekler dahil), iç saha/deplasman performansı, ve bunların sentezinden yüzdelik olasılık + tahmini skor.

## Kesin emirler (tüm diğer kurallardan üstün)

1. **Sahte veri/istatistik kesinlikle yasak.** Kaynağı doğrulanamayan hiçbir sayı, form bilgisi, sakatlık haberi rapora giremez. Bulunamazsa "bu bilgi doğrulanamadı" yazılır, uydurulmaz.
2. **Kesin sonuç iddiası yasak.** Sadece olasılık/yüzde dilinde konuşulur ("%X ihtimalle" gibi); "kesin kazanır", "garanti" gibi ifadeler kullanılmaz.
3. **En az 2 bağımsız kaynaktan çapraz doğrulama zorunlu** (özellikle kadro/sakatlık bilgisi için).
4. **Gerçek bahis işlemi yapılmaz.** Hiçbir ajan hiçbir bahis sitesinde işlem/para hareketi yapmaz; sadece analiz ve rapor üretir.
5. **Hata sessizce geçilmez.** Veri eksikliği/belirsizlik açıkça raporda belirtilir ("bu bilgi doğrulanamadı" / "veri yok").
6. **Sorumlu oyun uyarısı** her raporun sonunda yer alır.
7. **Bilgi bankası bütünlüğü:** `knowledge-curator` dışında hiçbir ajan `knowledge/` klasörüne doğrudan yazmaz. Çelişkili bilgi üzerine yazılmaz; tarihli not olarak eklenir.
8. **İlk yarı/maç sonucu (İY/MS) ayrı bir pazardır.** Maç sonucu (MS) oranları/olasılıkları İY/MS tahmini için kaynak sayılmaz — İY/MS için ayrıca, doğrudan kaynak kontrolü yapılır (ilk yarı gol istatistikleri, İY/MS'ye özel oran/tahmin kaynakları). Doğrudan kaynak bulunamazsa, MS modelinden + genel ilk yarı gol eğilimlerinden (kaynağı belirtilerek) türetilmiş bir tahmin sunulabilir ama bu **açıkça "türetilmiş tahmin, doğrudan kaynaklanmamıştır" notuyla** işaretlenir. **Her maçın analizinin sonuna, o maça özel bu notla birlikte İlk Yarı Sonucu ve Maç Sonucu (İY/MS) tahmini eklenir** — rapor formatına bakınız.
9. **Fikstür taraması eksiksiz olmalı — sabit lig listesi yasak.** `fixture-scanner` belirli, önceden tanımlı bir lig/turnuva listesiyle sınırlı kalamaz; o gün/gece **fiilen oynanan tüm ligleri** taramaya çalışır. Maçlar, kaynağın kullandığı tarih etiketine göre değil, **maçın gerçek başlama saatine göre** günün kapsamına dahil edilir — saat farkı yüzünden bir kaynağın "ertesi gün" olarak etiketlediği ama kullanıcının gecesine denk gelen maçlar atlanmaz (bkz. `agents/fixture-scanner.md`).

## Model metodolojisi (profesyonel yaklaşım — kalıcı, her koşuda uygulanır)

Bu sistem, profesyonel futbol tahmin modellerinin kullandığı yöntemleri taklit eder (araştırma kaynağı: dashee87.github.io, statsultra.com, scoresportsx.com — Dixon-Coles/Elo/ensemble literatürü). `statistical-model` ajanı her maçta aşağıdaki bileşenleri uygular:

1. **Dixon-Coles tipi Poisson modeli:** Her takım için atak gücü (attığı gol / lig ortalaması) ve savunma zayıflığı (yediği gol / lig ortalaması) parametreleri, iki bağımsız Poisson değişkeni olarak ev sahibi/deplasman beklenen gol sayısını (λ) üretir. Düşük skorlu sonuçlarda (0-0, 1-0, 0-1, 1-1) standart Poisson'un beraberlikleri hafife alma eğilimini düzeltmek için bu skorların olasılığı yukarı ayarlanır. Yakın tarihli maçlara daha fazla ağırlık verilir (son 5-10 maç, daha eski maçlardan daha belirleyici).
2. **Elo benzeri güç puanı:** Her takım için `knowledge/teams/<takım>.md` dosyasında bir "Güç puanı" alanı tutulur (varsayılan başlangıç: 1500). Her sonuçtan sonra `knowledge-curator`, beklenen sonuca göre puan transferi yapar — sürpriz sonuçlar (düşük puanlının yüksek puanlıyı yenmesi) puanı daha çok değiştirir, beklenen sonuçlar azını değiştirir. Bu puan farkı, maçın kazanma olasılığına dönüştürülüp modele girdi olarak kullanılır.
3. **Piyasa ile harmanlama (ensemble):** Poisson/Elo modelinin çıktısı, `odds-market-analyst`'ın zımni piyasa olasılığıyla harmanlanır. Veri zengin liglerde (çok kaynak, çok geçmiş maç) kendi modeline daha fazla ağırlık verilir; veri kıt liglerde piyasaya daha fazla ağırlık verilir. Büyük sapmalar gerekçelendirilir (rule: statistical-model çıktı formatı).
4. **Kalibrasyon takibi (self-improvement, artık otomatik):** Doğruluk (isabet) tek başına yeterli bir ölçüt değildir — asıl hedef **kalibrasyon**dur: modelin "%60 ihtimalle" dediği maçların gerçekten yaklaşık %60'ının o şekilde sonuçlanması. Kullanıcı "dünkü/geçmiş sonuçları güncelle" dediğinde **veya** kullanıcı "bugünün maçlarını analiz et" dediğinde akış başlamadan önce (bkz. Orkestrasyon akışı, adım 0), `knowledge/model-performance.md` içine önceki günlerin sonuçları best-effort işlenir. Kalibrasyon artık **hem genel hem de kırılım bazında** tutulur:
   - **Lig bazında:** her lig/turnuva için ayrı isabet ve kalibrasyon özeti (bir ligde model tutarlı şekilde iyi/kötüyse bu ayrı görülebilsin).
   - **Güven seviyesi bazında:** Düşük/Orta/Yüksek güven etiketlerinin her biri için ayrı gerçek isabet oranı (örn. "Yüksek güven" dediği maçların gerçekten en isabetli grup olup olmadığı).
   Model aşırı özgüvenliyse (yüksek yüzdeler verip tutmuyorsa) veya çekingense (düşük yüzdeler verip sürekli tutuyorsa), bir sonraki koşularda güven seviyesi/yüzdeler buna göre hafifçe ayarlanır ve bu ayarlama `model-performance.md`'de gerekçesiyle not edilir. `report-writer`, güncel kalibrasyon özetini rapora periyodik bir "📊 Geçmiş performans notu" olarak yansıtır (bkz. Rapor formatı).
5. **Kadro eksiklerinin önem ağırlıklandırması:** `squad-injury-scout`'un eksik oyuncuları kilit/rotasyon/önemsiz yedek olarak ayırması, modelin güç ayarlamasına doğrudan girdi olur — kilit oyuncu eksikliği gücü belirgin şekilde düşürür, rotasyon oyuncusu eksikliği hafif düşürür, önemsiz yedek eksikliği pratikte modeli değiştirmez. Bu ayarlamanın yönü ve büyüklüğü çıktıda kısaca belirtilir.
6. **Fikstür yoğunluğu, dinlenme günü ve motivasyon:** `team-form-analyst`'ın ilettiği dinlenme günü sayısı ve yorgunluk riski (kupa/Avrupa maçı sonrası darlık) modelin gücüne küçük bir düzeltme olarak yansır. Bir takımın o maçta kaybedecek/kazanacak bir şeyi kalmadığına dair sinyal (küme düşme/şampiyonluk hattı dışı, kupa önceliği düşük vb.) varsa maç **"dead rubber ihtimali"** olarak işaretlenir ve bu durum güven seviyesini düşürür (motivasyonsuz takımların davranışı istatistiksel olarak daha az öngörülebilir).
7. **Piyasa sapma sinyali:** Modelin ürettiği maç sonucu olasılığı ile `odds-market-analyst`'ten gelen zımni piyasa olasılığı arasındaki fark, tahmin edilen sonuç için **%15 puan veya daha fazlaysa**, bu maç raporda **"⚠️ Piyasadan belirgin ayrışan tahmin"** etiketiyle ayrıca işaretlenir ve fark yüzde puan olarak belirtilir. Amaç: bu maçların zamanla gerçekten daha mı isabetli/isabetsiz çıktığını `model-performance.md` üzerinden ayrıca izleyebilmek — piyasadan sapma kendi başına ne doğrulama ne yanlışlama değildir, sadece takip edilmesi gereken bir işarettir.

## Klasör yapısı

```
mac-tahmin-ordusu/
├── CLAUDE.md
├── mac-tahmin-ordusu-master-prompt.md
├── agents/                # subagent tanım dosyaları (referans/spesifikasyon)
├── knowledge/              # KALICI bilgi bankası
│   ├── teams/<takım>.md
│   ├── h2h/<takımA>-vs-<takımB>.md
│   └── model-performance.md
├── scripts/
├── logs/
│   ├── daily-runs/
│   ├── known-issues.md
│   └── agent-experience.jsonl
└── reports/YYYY-MM-DD-mac-analizleri.md
```

Bu repodaki `.claude/agents/` klasöründe, buradaki `agents/*.md` dosyalarıyla birebir aynı içerikte, Claude Code'un gerçekten çağırabildiği subagent tanımları bulunur (frontmatter: `name`, `description`, `tools`, `model`). İki kopyayı senkron tut — birinde değişiklik yapılırsa diğeri de güncellenir.

## Orkestrasyon akışı

Kullanıcı "bugünün maçlarını analiz et" dediğinde, ana oturum (sen) şu akışı Task/Agent aracıyla yürütür:

```
0. Otomatik kalibrasyon kontrolü (best-effort, engelleyici değil)
   └─ reports/ altında model-performance.md'ye henüz işlenmemiş geçmiş gün(ler) var mı kontrol et
   └─ varsa gerçek sonuçları ara, bulabildiklerini knowledge/model-performance.md'ye işle
   └─ bulunamazsa/zaman alıyorsa sessizce atla, ana akışı bekletme

fixture-scanner (günün/gecenin tüm maçları — gerçek başlama saatine göre, sabit lig listesi yok)
   └─ tarama biter bitmez: bulunan toplam maç sayısı + lig dağılımı logs/daily-runs/YYYY-MM-DD.md'ye ara log olarak yazılır
   └─ her maç için sırayla:
        squad-injury-scout (kilit/rotasyon/önemsiz ayrımıyla) ─┐
        team-form-analyst (+ fikstür yoğunluğu/dinlenme günü/motivasyon) ├─→ research-verifier ─→ statistical-model ─→ knowledge-curator
        h2h-analyst         │
        home-away-analyst   │
        tactical-style-analyst
        odds-market-analyst ┘
   └─ tüm maçlar bitince → report-writer → reports/YYYY-MM-DD-mac-analizleri.md
```

Kurallar:
- Her maç için önce ilgili `knowledge/teams/<takım>.md` ve `knowledge/h2h/<takımA>-vs-<takımB>.md` dosyaları okunur. 30 günden eski veya eksik bilgi varsa yalnızca o kısım taze araştırmayla güncellenir — sıfırdan başlanmaz.
- Bir ajan veri bulamaz veya hata verirse `error-debugger` çağrılır; süreç durmaz, o maç "veri eksik/belirsiz" notuyla devam eder.
- Tüm maçlar bitince `knowledge-curator` o günün tüm yeni bilgilerini bilgi bankasına işler, sonra `report-writer` nihai raporu yazar.
- Koşunun tam logu `logs/daily-runs/YYYY-MM-DD.md` içine yazılır; ajanların öz-değerlendirmesi `logs/agent-experience.jsonl` içine bir satır JSON olarak eklenir.
- Kullanıcı açıkça "dünkü/geçmiş sonuçları güncelle" derse aynı süreç manuel olarak da tetiklenebilir; adım 0'daki otomatik kontrol bunun yerini almaz, tamamlayıcısıdır (adım 0 best-effort ve sessizdir, manuel istekte ise sonuç kullanıcıya raporlanır).

## Rapor formatı

```
📅 <tarih> — Günün Maç Analizleri (X maç)

(varsa) 📊 Geçmiş performans notu: [model-performance.md'deki güncel lig/güven-seviyesi bazlı kalibrasyon özeti — kısa, 2-3 cümle. Yeterli veri yoksa bu bölüm atlanır.]

1) <Takım A> – <Takım B> (<Lig>, <saat>)
   Form: A son 5: ... | B son 5: ...
   H2H (son 5): ...
   Kadro: ... [kilit X, rotasyon Y, önemsiz yedek Z eksik — modele etkisi: ...]
   Fikstür/Motivasyon: [dinlenme günü farkı, yorgunluk riski] | [motivasyon durumu; varsa 🔻 Dead rubber ihtimali]
   Model tahmini (Maç Sonucu): A %.. – Beraberlik %.. – B %..
   Olası skor: .. / ..
   Güven seviyesi: ..
   Kaynaklar: [...]
   İlk Yarı / Maç Sonucu (İY/MS): İlk yarı A %.. – Beraberlik %.. – B %.. | En olası İY/MS kombinasyonu: .. / ..
   (Not: İY/MS ayrı bir pazardır — MS oranından türetilmemiştir; doğrudan kaynağı: [...]. Doğrudan kaynak yoksa: "türetilmiş tahmin, doğrudan kaynaklanmamıştır" notu.)
   (varsa) ⚠️ Piyasadan belirgin ayrışan tahmin: model %X – piyasa %Y (fark %Z puan)

2) ...

⚠️ Bu analizler istatistiksel modelleme ve güncel verilere dayanır, kesin sonuç garantisi değildir. Futbolda sürpriz her zaman mümkündür.
```

## Kullanım

Kullanıcı bu klasörde/proje bağlamında "bugünün maçlarını analiz et" dediğinde yukarıdaki akışı başlat. Zamanlanmış/otomatik tetikleme yoktur — sadece açık istek üzerine çalışır.
