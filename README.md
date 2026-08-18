# futbol-analiz-motoru

Futbol maçları için çoklu ajan (multi-agent) mimarisiyle çalışan, veri toplayan,
analiz eden ve olasılık tabanlı tahmin üreten bir sistem.

## İçerik

- **`ajan_ordusu/`** — Python çoklu ajan tahmin motoru (prototip). Ajanlar:
  - Veri Toplama (`agents/data_collection.py`) — football-data.org / OpenLigaDB çıktısını normalize eder
  - Form Analiz (`agents/form_analysis.py`) — son N maç performansı
  - H2H (`agents/h2h_analysis.py`) — iki takım arası geçmiş karşılaşmalar
  - Sakatlık/Kadro (`agents/squad_analysis.py`) — eksik/cezalı oyuncuların takım gücüne etkisini skorlar (API-Football)
  - Oran/Piyasa (`agents/market_analysis.py`) — gerçek bahis oranlarından zımni olasılıkları hesaplar (The Odds API)
  - Tahmin (`agents/prediction.py`) — form + H2H + kadro + piyasa etkisini birleştirip olasılık tabanlı tahmin üretir
  - Orkestratör (`agents/orchestrator.py`) — yukarıdakileri sırayla çalıştırıp tek maç için Markdown rapor üretir
  - Rapor & Bülten (`agents/bulletin.py`) — birden çok maçın sonucunu günlük/haftalık bültene dönüştürür;
    her maç için güven düzeyini, eksik veri uyarılarını ("VERİ YOK"/"Yetersiz Veri") ve risk uyarısını gösterir
  - Henüz eklenmedi: n8n ile zamanlanmış çalıştırma/dağıtım entegrasyonu
- **`index.html` + `api/matches.js`** — ayrı, mevcut basit JS/Vercel canlı skor arayüzü (ajan ordusundan bağımsız)

## Veri bütünlüğü kuralı (kesin)

Hiçbir ajan sahte, rastgele veya uydurma istatistik/veri üretmez. Tüm veriler
gerçek kaynaklardan gelir (OpenLigaDB, football-data.org, API-Football, The
Odds API). Bir maç/takım için gerçek veri bulunamazsa, ajan bunu sessizce
nötr bir sayıyla doldurmak yerine **açıkça "veri yok" / "yetersiz veri"**
olarak raporlar (ör. Sakatlık Ajanı'nda "Bilinmiyor" durumu, Tahmin
Ajanı'nda "Yetersiz Veri" güven düzeyi ve rapordaki "VERİ YOK" satırları).
`--demo` modu ağ/anahtar gerektirmeden pipeline'ı test etmek için tamamen
kurgusal veri kullanır ve bunu hem kod içinde hem çalışma zamanı çıktısında
açıkça belirtir — asla gerçek bir analiz gibi sunulmaz. Bu kural, eklenecek
tüm yeni ajanlar (Rapor & Bülten dahil) için de geçerlidir.

### Çalıştırma (ajan ordusu prototipi)

```bash
pip install -r requirements.txt

# Ağ/anahtar gerektirmeyen demo (kurgusal örnek veriyle uçtan uca pipeline testi):
python -m ajan_ordusu.main --demo

# Gerçek veri ile (football-data.org, ücretsiz kayıt gerektirir):
export FOOTBALL_DATA_API_TOKEN=...   # https://www.football-data.org/client/register
python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --home-name "..." --away-name "..."

# Sakatlık/kadro verisini de dahil etmek için (opsiyonel, API-Football ücretsiz plan):
export API_FOOTBALL_KEY=...          # https://www.api-football.com/pricing

# Oran/piyasa verisini de dahil etmek için (opsiyonel, The Odds API ücretsiz plan):
export THE_ODDS_API_KEY=...          # https://the-odds-api.com/
python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --sport-key soccer_epl

# Ağ/anahtar gerektirmeyen çok maçlı bülten örneği (biri eksik verili, uyarıları gösterir):
python -m ajan_ordusu.main --bulletin-demo

# Gerçek veriyle günlük/haftalık bülten (bir lig + tarih aralığındaki tüm maçlar):
python -m ajan_ordusu.main --bulletin --competition PL --date-from 2026-08-18 --date-to 2026-08-18

# Testler
pytest
```

Tahminler olasılık tabanlıdır, kesin sonuç garantisi vermez — bu uyarı her
raporun ve bültenin başında/sonunda otomatik olarak yer alır.

## api/matches.js hakkında not

Bu dosyada daha önce sabit kodlanmış (hardcoded) bir API anahtarı vardı; artık
`SPORTDB_API_KEY` ortam değişkeninden okunuyor. **Eski anahtar git geçmişinde
hâlâ görünür durumda — sağlayıcı tarafında iptal edilmesi/rotate edilmesi
gerekir.**
