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
  - `api.py` — n8n gibi orkestrasyon araçlarının çağırabilmesi için ince bir FastAPI HTTP sarmalayıcısı
- **`n8n/`** — n8n'e import edilecek iki workflow tanımı (self-hosted: dosyaya yazar; n8n Cloud:
  e-posta ile gönderir), `api.py`'yi günlük tetikler (bkz. `n8n/README.md`)
- **`index.html` + `api/matches.js`** — ayrı, mevcut basit JS/Vercel canlı skor arayüzü (ajan ordusundan bağımsız)
- **`mobile/`** — Expo/React Native mobil uygulama.
  - Zorunlu onboarding/sorumluluk reddi (disclaimer) akışı: kullanıcı "bahis
    tavsiyesi değildir, olasılık tabanlıdır, 18+" metnini kabul etmeden içeri
    giremez (`src/screens/OnboardingScreen.tsx`, `src/constants/legal.ts`).
  - Tahmin ekranı (`src/screens/PredictionScreen.tsx`) `ajan_ordusu/api.py`'ye
    bağlanır: açılışta `/bulletin/demo`'yu çeker (açıkça DEMO etiketli),
    eksik veri uyarılarını ve risk uyarısını olduğu gibi gösterir; "Gerçek Maç
    Sorgula" bölümünden takım ID/adı girilerek `/match` uç noktası
    sorgulanabilir. API adresi (⚙️ ikonu) cihazda kalıcı olarak ayarlanabilir
    — fiziksel cihazdan test ederken bilgisayarın LAN IP'si gerekir.

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

# HTTP API'yi başlat (n8n gibi araçların çağırması için, bkz. n8n/README.md):
uvicorn ajan_ordusu.api:app --host 0.0.0.0 --port 8000
```

Tahminler olasılık tabanlıdır, kesin sonuç garantisi vermez — bu uyarı her
raporun ve bültenin başında/sonunda otomatik olarak yer alır.

## n8n ile zamanlanmış çalıştırma

`n8n/futbol_bulten_workflow.json`, `api.py`'yi günde bir kez tetikleyip
bülteni bir Markdown dosyasına yazan hazır bir n8n workflow'udur. Kurulum ve
ortam değişkenleri için bkz. [`n8n/README.md`](n8n/README.md). Şu an için
dağıtım kanalı yalnızca dosya çıktısıdır; Telegram/Discord/e-posta gibi
mesajlaşma entegrasyonları kapsam dışıdır (bilinçli bir seçimdi, ileride
workflow'a tek bir node eklenerek genişletilebilir).

## api/matches.js hakkında not

Bu dosyada daha önce sabit kodlanmış (hardcoded) bir API anahtarı vardı; artık
`SPORTDB_API_KEY` ortam değişkeninden okunuyor. **Eski anahtar git geçmişinde
hâlâ görünür durumda — sağlayıcı tarafında iptal edilmesi/rotate edilmesi
gerekir.**
