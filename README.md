# futbol-analiz-motoru

Futbol maçları için çoklu ajan (multi-agent) mimarisiyle çalışan, veri toplayan,
analiz eden ve olasılık tabanlı tahmin üreten bir sistem.

## İçerik

- **`ajan_ordusu/`** — Python çoklu ajan tahmin motoru (prototip). Ajanlar:
  - Veri Toplama (`agents/data_collection.py`) — football-data.org / OpenLigaDB çıktısını normalize eder
  - Form Analiz (`agents/form_analysis.py`) — son N maç performansı
  - H2H (`agents/h2h_analysis.py`) — iki takım arası geçmiş karşılaşmalar
  - Tahmin (`agents/prediction.py`) — form + H2H'yi birleştirip olasılık tabanlı tahmin üretir
  - Orkestratör (`agents/orchestrator.py`) — yukarıdakileri sırayla çalıştırıp Markdown rapor üretir
  - Henüz eklenmedi: Sakatlık/Kadro Ajanı, Oran/Piyasa Ajanı, Rapor & Bülten Ajanı, n8n entegrasyonu
- **`index.html` + `api/matches.js`** — ayrı, mevcut basit JS/Vercel canlı skor arayüzü (ajan ordusundan bağımsız)

### Çalıştırma (ajan ordusu prototipi)

```bash
pip install -r requirements.txt

# Ağ/anahtar gerektirmeyen demo (kurgusal örnek veriyle uçtan uca pipeline testi):
python -m ajan_ordusu.main --demo

# Gerçek veri ile (football-data.org, ücretsiz kayıt gerektirir):
export FOOTBALL_DATA_API_TOKEN=...   # https://www.football-data.org/client/register
python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --home-name "..." --away-name "..."

# Testler
pytest
```

Tahminler olasılık tabanlıdır, kesin sonuç garantisi vermez — bu uyarı her
raporun sonunda otomatik olarak yer alır.

## api/matches.js hakkında not

Bu dosyada daha önce sabit kodlanmış (hardcoded) bir API anahtarı vardı; artık
`SPORTDB_API_KEY` ortam değişkeninden okunuyor. **Eski anahtar git geçmişinde
hâlâ görünür durumda — sağlayıcı tarafında iptal edilmesi/rotate edilmesi
gerekir.**
