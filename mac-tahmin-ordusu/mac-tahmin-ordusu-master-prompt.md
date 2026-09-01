# Maç Tahmin Ordusu — Claude Code Kurulum Promptu

Bu dosyayı olduğu gibi Claude Code'a yapıştırıp "bunu kur" diyebilirsin. Etsy ordusundan (`agent-ordusu/`) tamamen bağımsız, ayrı bir proje klasörüdür — hiçbir dosya veya ajan iki proje arasında paylaşılmaz.

## 1. Amaç

Kullanıcı günün herhangi bir saatinde "bugünün maçlarını analiz et" dediğinde, bir agent ordusu devreye girer; o gün oynanacak **tüm liglerdeki tüm futbol maçlarını** tek tek, gerçek bir spor analistinin yaptığı a'dan z'ye analiz sürecini taklit ederek inceler ve sonunda kullanıcıya **tüm maçları alt alta sıralayan tek bir rapor** sunar. Her maç için: form durumu, ikili geçmiş (h2h), kadro/sakatlık/ceza durumu (yedekler dahil), iç saha-deplasman performansı, ve bunların sentezinden çıkan **yüzdelik olasılık + tahmini skor**.

Sistem zamanla **kendi kendini geliştirir**: her koşuda öğrendiği her şeyi (takım kadroları, yedek oyuncular, form eğilimleri, oynanan taktik, sakatlık geçmişi) kalıcı bir bilgi bankasına kaydeder ve bir sonraki koşuda oradan başlar — sıfırdan araştırmaz, üstüne ekler.

## 2. Klasör yapısı

Proje kökü `agent-ordusu` ile **aynı üst dizinde, ayrı bir klasör** olarak açılır (örn. Masaüstü altında):

```
mac-tahmin-ordusu/
├── CLAUDE.md                      # kesin emirler — tüm ajanları bağlar
├── mac-tahmin-ordusu-master-prompt.md   # bu dosyanın kopyası (referans)
├── agents/                        # her subagent'ın kendi .md tanım dosyası
│   ├── fixture-scanner.md
│   ├── team-form-analyst.md
│   ├── h2h-analyst.md
│   ├── squad-injury-scout.md
│   ├── home-away-analyst.md
│   ├── tactical-style-analyst.md
│   ├── odds-market-analyst.md
│   ├── statistical-model.md
│   ├── research-verifier.md
│   ├── knowledge-curator.md
│   ├── report-writer.md
│   └── error-debugger.md
├── knowledge/                     # KALICI bilgi bankası — gün geçtikçe zenginleşir
│   ├── teams/
│   │   └── <takım-adı>.md         # kadro (11 + yedekler), form geçmişi, taktik notlar, son güncelleme tarihi
│   ├── h2h/
│   │   └── <takımA>-vs-<takımB>.md
│   └── model-performance.md       # geçmiş tahminlerin tuttu/tutmadı takibi (kendini değerlendirme)
├── scripts/                       # orkestrasyon ve yardımcı scriptler
├── logs/
│   ├── daily-runs/                # her günün tam çalışma logu
│   ├── known-issues.md
│   └── agent-experience.jsonl     # ajanların öz-değerlendirmesi (self-review)
└── reports/
    └── YYYY-MM-DD-mac-analizleri.md   # o günün nihai raporu
```

## 3. Kalıcı bilgi bankası (öğrenme mekanizması)

Kullanıcı isteği: sistem "kendi kendini geliştirsin", takımları yedek oyunculara kadar "ezberlesin". Bunu şöyle karşılıyoruz:

- Her takım için `knowledge/teams/<takım>.md` dosyası vardır. İlk analizde sıfırdan oluşturulur; sonraki her analizde **research-verifier'dan geçmiş yeni bilgiyle güncellenir**, üzerine yazılmaz.
- Dosya içeriği: güncel kadro (ilk 11 + kulübedeki yedekler + kadro dışı/sakat/cezalı liste), son 10 maç formu, tipik dizilişi, dikkat çeken taktik eğilimler, bilinen zayıf/güçlü yönler, veri kaynakları ve her bilginin **son doğrulama tarihi**.
- **knowledge-curator** ajanının tek görevi budur: her koşudan sonra yeni öğrenilenleri ilgili takım dosyasına düzgün şekilde eklemek/güncellemek, çelişkileri işaretlemek, eskimiş (>30 gün) bilgiyi "doğrulanması gerekiyor" olarak etiketlemek.
- `knowledge/model-performance.md`: geçmişte verilen tahminlerin gerçek sonuçla karşılaştırması (maç oynandıktan sonra otomatik değil, kullanıcı "dünkü sonuçları güncelle" dediğinde) — model zamanla hangi lig/durumda daha isabetli olduğunu görür, bu da rapora "geçmiş performans notu" olarak yansıyabilir.
- Böylece 30. günde bir takım için sıfırdan araştırma yapılmaz; bilgi bankası okunur, sadece **değişen kısımlar** (yeni sakatlık, yeni sonuç, yeni transfer) taze araştırmayla güncellenir. Bu hem hızı hem isabeti artırır.

## 4. Ajanlar ve görevleri

1. **fixture-scanner** — o günün tüm liglerdeki maç programını çıkarır (takımlar, lig, saat, statü/ertelenme).
2. **team-form-analyst** — her iki takımın son 5-10 maçlık formu, gol/yenilen gol ortalaması, xG (varsa).
3. **h2h-analyst** — iki takımın geçmiş karşılaşmaları, saha faktörü dahil eğilimler.
4. **squad-injury-scout** — güncel kadro, sakatlar, cezalılar, muhtemel ilk 11 ve **yedek kulübesi**; `knowledge/teams/` dosyasını okuyup güncelliğini kontrol eder, gerekirse taze araştırma yapar.
5. **home-away-analyst** — iç saha/deplasman ayrı performans farkları.
6. **tactical-style-analyst** — oyun stili, baskı/pas eğilimleri (kaynak bulunabildiği ölçüde; bulunamazsa "veri yok" der, uydurmaz).
7. **odds-market-analyst** — açık bahis oranlarını toplar, implied probability çıkarır (piyasanın ne düşündüğünü referans olarak kullanmak için — kendi modelin piyasadan ne kadar ayrıştığını göstermek amacıyla, kopyalamak için değil).
8. **statistical-model** — yukarıdaki tüm verileri sentezleyip olasılıksal bir model (ör. Poisson/ELO tabanlı) ile ev sahibi/beraberlik/deplasman yüzdelerini ve olası skor aralığını hesaplar.
9. **research-verifier** — her sayısal iddianın gerçek kaynaktan geldiğini doğrular; kaynağı doğrulanamayan hiçbir veri rapora giremez.
10. **knowledge-curator** — yukarıda anlatıldığı gibi bilgi bankasını günceller.
11. **report-writer** — nihai Türkçe raporu, aşağıdaki formatta, günün **tüm maçlarını alt alta sıralayarak** yazar.
12. **error-debugger** — bir ajan hata verirse veya veri bulunamazsa devreye girer; sessizce atlamak yerine durumu rapora "bu maç için X verisi doğrulanamadı" şeklinde not düşer.

## 5. Orkestrasyon akışı

Kullanıcı "bugünün maçlarını analiz et" dediğinde:

```
fixture-scanner (günün tüm maçları)
   └─ her maç için sırayla:
        squad-injury-scout ─┐
        team-form-analyst   ├─→ research-verifier ─→ statistical-model ─→ knowledge-curator
        h2h-analyst         │
        home-away-analyst   │
        tactical-style-analyst
        odds-market-analyst ┘
   └─ tüm maçlar bitince → report-writer → reports/YYYY-MM-DD-mac-analizleri.md
```

Hata olursa `error-debugger` çağrılır, o maç için "belirsiz/veri eksik" notuyla devam edilir, süreç durmaz.

## 6. Rapor formatı (örnek)

```
📅 19 Ağustos 2026 — Günün Maç Analizleri (X maç)

1) Galatasaray – Fenerbahçe (Süper Lig, 19:00)
   Form: GS son 5: G-G-B-G-M | FB son 5: G-B-G-G-G
   H2H (son 5): 2 GS, 1 FB, 2 Beraberlik
   Kadro: GS'de X sakat, Y cezalı; FB'de kadro tam
   Model tahmini: GS %42 – Beraberlik %27 – FB %31
   Olası skor: 2-1 / 1-1
   Güven seviyesi: Orta (kadro netliği nedeniyle)
   Kaynaklar: [liste]

2) ...

⚠️ Bu analizler istatistiksel modelleme ve güncel verilere dayanır, kesin sonuç garantisi değildir. Futbolda sürpriz her zaman mümkündür.
```

## 7. CLAUDE.md — kesin emirler (tüm diğer kurallardan üstün)

- **Sahte veri/istatistik kesinlikle yasak.** Kaynağı doğrulanamayan hiçbir sayı, form bilgisi, sakatlık haberi rapora giremez. Bulunamazsa "bu bilgi doğrulanamadı" yazılır, uydurulmaz.
- **Kesin sonuç iddiası yasak.** Sadece olasılık/yüzde dilinde konuşulur ("%X ihtimalle" gibi); "kesin kazanır", "garanti" gibi ifadeler kullanılmaz.
- **En az 2 bağımsız kaynaktan çapraz doğrulama** zorunlu (özellikle kadro/sakatlık bilgisi için).
- **Gerçek bahis işlemi yapılmaz.** Ajanlar hiçbir bahis sitesinde işlem/para hareketi yapmaz; sadece analiz ve rapor üretir.
- **Hata sessizce geçilmez.** Veri eksikliği/belirsizlik açıkça raporda belirtilir.
- **Sorumlu oyun uyarısı** her raporun sonunda yer alır.
- **Bilgi bankası bütünlüğü:** knowledge-curator dışında hiçbir ajan `knowledge/` klasörüne doğrudan yazmaz; çelişkili bilgi üzerine yazılmaz, tarihli not olarak eklenir.

## 8. Kurulum

1. Bu dosyayı `mac-tahmin-ordusu/` adında yeni, boş bir klasöre koy (agent-ordusu'nun içine değil, yanına).
2. Claude Code'u o klasörde aç, bu dosyanın içeriğini yapıştır: "Bu master prompt'a göre projeyi kur: CLAUDE.md, agents/, knowledge/, scripts/, logs/, reports/ klasörlerini ve subagent tanım dosyalarını oluştur."
3. İlk çalıştırmada bilgi bankası boş olacağı için ilk analiz biraz daha uzun sürer (sıfırdan araştırma); sonraki günlerde bilgi bankası büyüdükçe hızlanır ve derinleşir.
4. Zamanlanmış görev istemiyorsan (kullanıcı tercihi: manuel tetikleme) Windows Görev Zamanlayıcısı'na hiçbir şey eklenmez — sadece sen "bugünün maçlarını analiz et" dediğinde çalışır.
