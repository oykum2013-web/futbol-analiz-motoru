# futbol-analiz-motoru

Futbol maçları için çoklu ajan (multi-agent) mimarisiyle çalışan, veri toplayan,
analiz eden ve olasılık tabanlı tahmin üreten bir sistem.

## İçerik

- **`ajan_ordusu/`** — Python çoklu ajan tahmin motoru (prototip). Ajanlar:
  - Veri Toplama (`agents/data_collection.py`) — football-data.org / OpenLigaDB çıktısını normalize eder
  - Form Analiz (`agents/form_analysis.py`) — son N maç performansı
  - H2H (`agents/h2h_analysis.py`) — iki takım arası geçmiş karşılaşmalar
  - Sakatlık/Kadro (`agents/squad_analysis.py`) — eksik/cezalı oyuncuların takım gücüne etkisini skorlar (API-Football)
  - Puan Durumu (`agents/standings_analysis.py`) — iki takımın güncel lig tablosundaki sırasını/puanını
    karşılaştırır (football-data.org); Form Ajanı'ndan farklı olarak son N maç değil, tüm sezonun performansını yansıtır
  - Oran/Piyasa (`agents/market_analysis.py`) — gerçek bahis oranlarından zımni olasılıkları hesaplar (The Odds API)
  - Web Araştırma (`agents/web_research.py`) — API'si olmayan/JS ile render edilen herhangi bir sayfayı
    gerçek bir Chromium tarayıcısıyla (Playwright) ziyaret edip ham metnini rapora ek bölüm olarak ekler
    (bkz. `--web-url`); yapılandırılmış tahmine dahil edilmez, sadece ek bağlam sunar
  - Mackolik Puan Durumu (`agents/mackolik_standings.py`) — football-data.org'un ücretsiz planında
    olmayan ligler (ör. Türkiye Süper Lig) için mackolik.com'un puan durumu sayfasını Chromium ile
    çekip yapılandırılmış bir tabloya (Markdown) dönüştürür (bkz. `--mackolik-standings-url`);
    API anahtarı gerektirmez
  - Tahmin (`agents/prediction.py`) — form + H2H + kadro + puan durumu + piyasa etkisini birleştirip
    olasılık tabanlı tahmin üretir
  - Doğrulama/Hata Kontrolü (`agents/validation.py`) — tahmin ajanının çıktısını iç tutarlılık hataları için
    denetler (olasılık toplamı 100 değil mi, güven düzeyi eldeki veriyle çelişiyor mu vb.); güvenle
    düzeltilebilen hatalar (ör. yuvarlama sapması) otomatik düzeltilir, düzeltilemeyenler rapora
    "❌ DÜZELTİLEMEDİ" olarak açıkça yazılır — hiçbir hata sessizce geçilmez
  - Orkestratör (`agents/orchestrator.py`) — yukarıdakileri sırayla çalıştırıp tek maç için Markdown rapor üretir
  - Rapor & Bülten (`agents/bulletin.py`) — birden çok maçın sonucunu günlük/haftalık bültene dönüştürür;
    her maç için güven düzeyini, eksik veri uyarılarını ("VERİ YOK"/"Yetersiz Veri") ve risk uyarısını gösterir
  - `api.py` — n8n gibi orkestrasyon araçlarının çağırabilmesi için ince bir FastAPI HTTP sarmalayıcısı
- **`n8n/`** — n8n'e import edilecek iki workflow tanımı (self-hosted: dosyaya yazar; n8n Cloud:
  e-posta ile gönderir), `api.py`'yi günlük tetikler (bkz. `n8n/README.md`)
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

# Raporu ekranın yanında bir dosyaya da kaydetmek için (--output her modla kullanılabilir):
python -m ajan_ordusu.main --demo --output rapor.md

# Gerçek veriyle günlük/haftalık bülten (bir lig + tarih aralığındaki tüm maçlar):
python -m ajan_ordusu.main --bulletin --competition PL --date-from 2026-08-18 --date-to 2026-08-18

# "Sıradaki N maçı analiz et" — tarih aralığı hesaplamaya gerek kalmadan, bugünden
# itibaren henüz oynanmamış ilk N fikstürü otomatik bulup hepsini analiz eder:
python -m ajan_ordusu.main --bulletin --competition PL --next 20

# Puan durumunu da tahmine dahil etmek için tek maç modunda da --competition verilebilir:
python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --competition PL

# Tam otomatik bülten — sadece lig kodu verilir; tarih aralığı, sıradaki fikstür sayısı
# ve çıktı dosya adı (bulten_<LIG>_<tarih>.md) elle girilmeden otomatik doldurulur:
python -m ajan_ordusu.main --bulletin-auto --competition TSL

# Chromium (Playwright) ile herhangi bir sayfayı ziyaret edip ham metnini rapora eklemek için
# (opsiyonel; kurulum: pip install playwright && playwright install chromium):
python -m ajan_ordusu.main --demo --web-url https://ornek-site.com/haber

# Türkiye Süper Lig gibi football-data.org'un ücretsiz planında olmayan ligler için:
# mackolik.com'dan gerçek, yapılandırılmış puan durumu tablosu (API anahtarı gerekmez):
python -m ajan_ordusu.main --mackolik-standings-url "https://www.mackolik.com/puan-durumu/türkiye-trendyol-süper-lig/2026-2027/482ofyysbdbeoxauk19yg7tdt"

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
