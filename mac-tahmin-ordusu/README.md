# mac-tahmin-ordusu

Claude Code subagent ordusu ile çalışan, günün tüm liglerdeki futbol maçlarını tek tek analiz edip tek bir raporda toplayan sistem. Bu repodaki `ajan_ordusu/` (Python prototipi) ile **ilgisi yoktur** — tamamen ayrı, bağımsız bir yaklaşımdır: burada "ajanlar" Claude Code subagent tanımlarıdır (`.claude/agents/*.md`), Python kodu değil.

Tasarım dokümanı: [`mac-tahmin-ordusu-master-prompt.md`](./mac-tahmin-ordusu-master-prompt.md)
Kurallar ve orkestrasyon akışı: [`CLAUDE.md`](./CLAUDE.md)

## Kullanım

Bu repoda (veya `mac-tahmin-ordusu/` dizininde) bir Claude Code oturumunda:

```
bugünün maçlarını analiz et
```

demen yeterli. Claude Code, `CLAUDE.md`'deki orkestrasyon akışını izleyerek:

1. `fixture-scanner` ile günün tüm maçlarını bulur,
2. her maç için `squad-injury-scout`, `team-form-analyst`, `h2h-analyst`, `home-away-analyst`, `tactical-style-analyst`, `odds-market-analyst` ajanlarını çalıştırır,
3. çıktıları `research-verifier` ile doğrular,
4. `statistical-model` ile olasılık/skor tahmini üretir,
5. `knowledge-curator` ile bilgi bankasını (`knowledge/`) günceller,
6. son olarak `report-writer` ile `reports/YYYY-MM-DD-mac-analizleri.md` dosyasını yazar.

Bir ajan veri bulamaz/hata verirse `error-debugger` devreye girer, süreç durmaz — o maç için "veri eksik/belirsiz" notu düşülür.

Zamanlanmış/otomatik tetikleme yoktur; sadece açık istek üzerine çalışır.

## Bilgi bankası

Sistem kendi kendini geliştirir: `knowledge/teams/<takım>.md` ve `knowledge/h2h/<takımA>-vs-<takımB>.md` dosyaları her koşuda güncellenir, üzerine yazılmaz. İlk çalıştırma bilgi bankası boş olduğu için daha uzun sürer; sonraki günlerde bilgi bankası büyüdükçe hızlanır.

`knowledge/model-performance.md` içine "dünkü sonuçları güncelle" dendiğinde geçmiş tahminlerin isabet durumu işlenir.

## Klasör yapısı

```
mac-tahmin-ordusu/
├── CLAUDE.md
├── mac-tahmin-ordusu-master-prompt.md
├── agents/            # subagent spesifikasyonları (.claude/agents/ ile birebir senkron)
├── knowledge/
│   ├── teams/
│   ├── h2h/
│   └── model-performance.md
├── scripts/
├── logs/
│   ├── daily-runs/
│   ├── known-issues.md
│   └── agent-experience.jsonl
└── reports/
```

Gerçekte çağrılabilen subagent tanımları repo kökündeki `.claude/agents/` altındadır; buradaki `agents/` klasörü aynı içeriğin proje-içi referans kopyasıdır (bkz. `CLAUDE.md`).

## Kesin kurallar

Bkz. `CLAUDE.md` — sahte veri yasak, kesin sonuç iddiası yasak, çapraz kaynak doğrulama zorunlu, gerçek bahis işlemi yapılmaz, hata sessizce geçilmez, sorumlu oyun uyarısı her raporda yer alır.
