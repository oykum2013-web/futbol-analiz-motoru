# n8n Entegrasyonu — Günlük Bülten Workflow'u

Bu klasördeki `futbol_bulten_workflow.json`, `ajan_ordusu` pipeline'ını günde
bir kez otomatik çalıştırıp bülteni bir Markdown dosyasına yazan bir n8n
workflow'udur.

**Not:** `oykum2013-web/n8n` reposu n8n platformunun kendisinin değiştirilmemiş
bir fork'udur — bu workflow onun içine değil, kendi self-hosted n8n
örneğinize *import edilecek* bağımsız bir dosyadır.

## Mimari

```
Cron (08:00) → HTTP Request (GET /bulletin) → Markdown'a Dönüştür → Dosyaya Yaz
```

n8n, bültenin kendisini üretmez — sadece zamanlar ve tetikler. Gerçek analiz
(veri toplama, form/H2H/kadro/oran/tahmin) her zaman olduğu gibi
`ajan_ordusu` Python paketinde, `api.py` üzerinden HTTP ile sunulur.

Şu an için dağıtım kanalı **yalnızca dosya/Markdown çıktısıdır** — Telegram/
Discord/e-posta entegrasyonu bilinçli olarak kapsam dışı bırakıldı. İleride
eklemek için son node'dan (Dosyaya Yaz) sonra ilgili n8n node'unu (Telegram,
Discord, Send Email) eklemeniz ve `markdown` alanını (ya da `matches`
dizisini) ona bağlamanız yeterli.

## Kurulum

### 1. API'yi çalıştırın

API, n8n'in erişebileceği bir yerde (aynı sunucu/container, veya ağ
üzerinden erişilebilir bir adres) çalışıyor olmalı:

```bash
pip install -r requirements.txt
export FOOTBALL_DATA_API_TOKEN=...      # zorunlu — https://www.football-data.org/client/register
export API_FOOTBALL_KEY=...             # opsiyonel — sakatlık/kadro verisi için
export THE_ODDS_API_KEY=...             # opsiyonel — oran/piyasa verisi için
uvicorn ajan_ordusu.api:app --host 0.0.0.0 --port 8000
```

Anahtarsız/veri bulunamayan durumlarda API sahte veri üretmez — ilgili
alanlar "VERİ YOK"/"Yetersiz Veri" olarak JSON'da görünür (bkz. kök
README'deki "Veri bütünlüğü kuralı").

### 2. n8n ortam değişkenlerini tanımlayın

n8n'in çalıştığı ortamda (ör. `docker-compose.yml`'de `environment:` altında
veya n8n'in kendi Settings → Variables ekranında — self-hosted sürümlerde
process ortam değişkeni olarak tanımlamak gerekir):

| Değişken | Açıklama | Örnek |
|---|---|---|
| `AJAN_ORDUSU_API_URL` | API'nin n8n'den erişilebilir adresi | `http://ajan-ordusu-api:8000` |
| `AJAN_ORDUSU_COMPETITION` | football-data.org lig kodu | `PL` |
| `AJAN_ORDUSU_SEASON` | API-Football sezon yılı | `2025` |
| `AJAN_ORDUSU_SPORT_KEY` | The Odds API lig anahtarı (opsiyonel — boş bırakılırsa oran verisi atlanır) | `soccer_epl` |
| `AJAN_ORDUSU_OUTPUT_DIR` | Bültenin yazılacağı, n8n container'ının erişebildiği (mount edilmiş) dizin | `/data/bulletins` |

`AJAN_ORDUSU_OUTPUT_DIR` n8n container'ından yazılabilir bir volume'a mount
edilmiş olmalı, aksi hâlde "Dosyaya Yaz" adımı hata verir.

### 3. Workflow'u import edin

n8n arayüzünde: **Workflows → Import from File** → `futbol_bulten_workflow.json`
dosyasını seçin.

Node tip sürümleri (`typeVersion`) makul, güncel bir n8n sürümüne göre
yazılmıştır; import sırasında bir uyumsuzluk uyarısı görürseniz n8n genelde
otomatik günceller — sorun devam ederse ilgili node'u arayüzden silip aynı
işlevi gören güncel node'u (HTTP Request, Convert to File, Read/Write Files
from Disk) elle ekleyip aynı parametreleri girmeniz yeterlidir.

### 4. Test edin

Workflow'u içe aktardıktan sonra sağ üstten **Execute Workflow** ile manuel
tetikleyip `AJAN_ORDUSU_OUTPUT_DIR` altında `bulten-YYYY-AA-GG.md` dosyasının
oluştuğunu doğrulayın. Ağ/anahtar olmadan hızlı bir uçtan uca test için
`AJAN_ORDUSU_API_URL`'i `/bulletin` yerine `/bulletin/demo` döndürecek şekilde
geçici olarak değiştirip (HTTP Request node'unun URL'sini elle düzenleyerek)
kurgusal veriyle deneme yapabilirsiniz.

### Zamanlamayı değiştirmek

"Günlük Tetikleyici" node'undaki cron ifadesini (`0 8 * * *`) n8n arayüzünden
değiştirebilirsiniz — ör. haftalık bülten için `0 8 * * 1` (her Pazartesi 08:00).
