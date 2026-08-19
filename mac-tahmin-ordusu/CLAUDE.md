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
   Model tahmini: A %.. – Beraberlik %.. – B %..
   Olası skor: .. / ..
   Güven seviyesi: ..
   Kaynaklar: [...]

2) ...

⚠️ Bu analizler istatistiksel modelleme ve güncel verilere dayanır, kesin sonuç garantisi değildir. Futbolda sürpriz her zaman mümkündür.
```

## Kullanım

Kullanıcı bu klasörde/proje bağlamında "bugünün maçlarını analiz et" dediğinde yukarıdaki akışı başlat. Zamanlanmış/otomatik tetikleme yoktur — sadece açık istek üzerine çalışır.
