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

## Model metodolojisi (profesyonel yaklaşım — kalıcı, her koşuda uygulanır)

Bu sistem, profesyonel futbol tahmin modellerinin kullandığı yöntemleri taklit eder (araştırma kaynağı: dashee87.github.io, statsultra.com, scoresportsx.com — Dixon-Coles/Elo/ensemble literatürü). `statistical-model` ajanı her maçta şu dört bileşeni uygular:

1. **Dixon-Coles tipi Poisson modeli:** Her takım için atak gücü (attığı gol / lig ortalaması) ve savunma zayıflığı (yediği gol / lig ortalaması) parametreleri, iki bağımsız Poisson değişkeni olarak ev sahibi/deplasman beklenen gol sayısını (λ) üretir. Düşük skorlu sonuçlarda (0-0, 1-0, 0-1, 1-1) standart Poisson'un beraberlikleri hafife alma eğilimini düzeltmek için bu skorların olasılığı yukarı ayarlanır. Yakın tarihli maçlara daha fazla ağırlık verilir (son 5-10 maç, daha eski maçlardan daha belirleyici).
2. **Elo benzeri güç puanı:** Her takım için `knowledge/teams/<takım>.md` dosyasında bir "Güç puanı" alanı tutulur (varsayılan başlangıç: 1500). Her sonuçtan sonra `knowledge-curator`, beklenen sonuca göre puan transferi yapar — sürpriz sonuçlar (düşük puanlının yüksek puanlıyı yenmesi) puanı daha çok değiştirir, beklenen sonuçlar azını değiştirir. Bu puan farkı, maçın kazanma olasılığına dönüştürülüp modele girdi olarak kullanılır.
3. **Piyasa ile harmanlama (ensemble):** Poisson/Elo modelinin çıktısı, `odds-market-analyst`'ın zımni piyasa olasılığıyla harmanlanır. Veri zengin liglerde (çok kaynak, çok geçmiş maç) kendi modeline daha fazla ağırlık verilir; veri kıt liglerde piyasaya daha fazla ağırlık verilir. Büyük sapmalar gerekçelendirilir (rule: statistical-model çıktı formatı).
4. **Kalibrasyon takibi (self-improvement):** Doğruluk (isabet) tek başına yeterli bir ölçüt değildir — asıl hedef **kalibrasyon**dur: modelin "%60 ihtimalle" dediği maçların gerçekten yaklaşık %60'ının o şekilde sonuçlanması. Kullanıcı "dünkü/geçmiş sonuçları güncelle" dediğinde, `knowledge/model-performance.md` içine sonuçlar işlenir ve basit bir kalibrasyon özeti çıkarılır (örn. "%50-60 aralığında tahmin edilen maçların gerçek isabet oranı %X"). Model aşırı özgüvenliyse (yüksek yüzdeler verip tutmuyorsa) veya çekingense (düşük yüzdeler verip sürekli tutuyorsa), bir sonraki koşularda güven seviyesi/yüzdeler buna göre hafifçe ayarlanır ve bu ayarlama `model-performance.md`'de gerekçesiyle not edilir.

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

Kurallar:
- Her maç için önce ilgili `knowledge/teams/<takım>.md` ve `knowledge/h2h/<takımA>-vs-<takımB>.md` dosyaları okunur. 30 günden eski veya eksik bilgi varsa yalnızca o kısım taze araştırmayla güncellenir — sıfırdan başlanmaz.
- Bir ajan veri bulamaz veya hata verirse `error-debugger` çağrılır; süreç durmaz, o maç "veri eksik/belirsiz" notuyla devam eder.
- Tüm maçlar bitince `knowledge-curator` o günün tüm yeni bilgilerini bilgi bankasına işler, sonra `report-writer` nihai raporu yazar.
- Koşunun tam logu `logs/daily-runs/YYYY-MM-DD.md` içine yazılır; ajanların öz-değerlendirmesi `logs/agent-experience.jsonl` içine bir satır JSON olarak eklenir.
- Kullanıcı "dünkü sonuçları güncelle" derse, `knowledge/model-performance.md` gerçek sonuçlarla güncellenir (bu adım otomatik tetiklenmez).

## Rapor formatı

```
📅 <tarih> — Günün Maç Analizleri (X maç)

1) <Takım A> – <Takım B> (<Lig>, <saat>)
   Form: A son 5: ... | B son 5: ...
   H2H (son 5): ...
   Kadro: ...
   Model tahmini (Maç Sonucu): A %.. – Beraberlik %.. – B %..
   Olası skor: .. / ..
   Güven seviyesi: ..
   Kaynaklar: [...]
   İlk Yarı / Maç Sonucu (İY/MS): İlk yarı A %.. – Beraberlik %.. – B %.. | En olası İY/MS kombinasyonu: .. / ..
   (Not: İY/MS ayrı bir pazardır — MS oranından türetilmemiştir; doğrudan kaynağı: [...]. Doğrudan kaynak yoksa: "türetilmiş tahmin, doğrudan kaynaklanmamıştır" notu.)

2) ...

⚠️ Bu analizler istatistiksel modelleme ve güncel verilere dayanır, kesin sonuç garantisi değildir. Futbolda sürpriz her zaman mümkündür.
```

## Kullanım

Kullanıcı bu klasörde/proje bağlamında "bugünün maçlarını analiz et" dediğinde yukarıdaki akışı başlat. Zamanlanmış/otomatik tetikleme yoktur — sadece açık istek üzerine çalışır.
