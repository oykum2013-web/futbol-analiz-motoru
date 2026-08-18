# n8n Entegrasyonu — Günlük Bülten Workflow'u

Bu klasörde iki workflow var; ikisi de aynı işi yapar (bülteni günde bir kez
üretip size ulaştırır), sadece n8n'in nerede çalıştığına göre farklı bir son
adım kullanırlar:

| Dosya | n8n nerede çalışıyor | Son adım |
|---|---|---|
| `futbol_bulten_workflow.json` | Kendi bilgisayarınızda/sunucunuzda (self-hosted, ör. Docker) | Bülteni yerel bir dosyaya yazar |
| `futbol_bulten_workflow_cloud.json` | n8n Cloud (n8n'in kendi barındırdığı, hesap açarak kullandığınız sürüm) | Bülteni size e-posta eki olarak gönderir |

n8n Cloud'un sizin bilgisayarınızda/sunucunuzda dosya yazma yetkisi yoktur,
bu yüzden self-hosted olmayan kurulumlarda dosya yerine e-posta kullanılır —
mesajlaşma servisi (Telegram/Discord) değil, sadece dosyanın size ulaşmasının
bulut-uyumlu hâli.

**Not:** `oykum2013-web/n8n` reposu n8n platformunun kendisinin değiştirilmemiş
bir fork'udur — bu workflow'lar onun içine değil, kendi n8n örneğinize
*import edilecek* bağımsız dosyalardır.

## Mimari

```
Cron (08:00) → HTTP Request (GET /bulletin) → Markdown'a Dönüştür → Dosyaya Yaz / E-postayla Gönder
```

n8n, bültenin kendisini üretmez — sadece zamanlar ve tetikler. Gerçek analiz
(veri toplama, form/H2H/kadro/oran/tahmin) her zaman olduğu gibi
`ajan_ordusu` Python paketinde, `api.py` üzerinden HTTP ile sunulur.

## Kurulum — ortak adım: API'yi çalıştırın

API, n8n'in erişebileceği bir yerde (ör. Render gibi bir barındırma
hizmetinde) çalışıyor olmalı:

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

---

## Seçenek A — Self-hosted (`futbol_bulten_workflow.json`)

### Ortam değişkenleri

n8n'in çalıştığı ortamda (ör. Docker `-e` parametreleriyle) tanımlayın:

| Değişken | Açıklama | Örnek |
|---|---|---|
| `AJAN_ORDUSU_API_URL` | API'nin n8n'den erişilebilir adresi | `https://futbol-analiz-motoru.onrender.com` |
| `AJAN_ORDUSU_COMPETITION` | football-data.org lig kodu | `PL` |
| `AJAN_ORDUSU_SEASON` | API-Football sezon yılı | `2025` |
| `AJAN_ORDUSU_SPORT_KEY` | The Odds API lig anahtarı (opsiyonel — boş bırakılırsa oran verisi atlanır) | `soccer_epl` |
| `AJAN_ORDUSU_OUTPUT_DIR` | Bültenin yazılacağı, n8n container'ının erişebildiği (mount edilmiş) dizin | `/data/bulletins` |

`AJAN_ORDUSU_OUTPUT_DIR` n8n container'ından yazılabilir bir volume'a mount
edilmiş olmalı, aksi hâlde "Dosyaya Yaz" adımı hata verir.

### Import ve test

n8n arayüzünde: **Workflows → Import from File** → `futbol_bulten_workflow.json`.
İçe aktardıktan sonra **Execute Workflow** ile tetikleyip
`AJAN_ORDUSU_OUTPUT_DIR` altında `bulten-YYYY-AA-GG.md` dosyasının oluştuğunu
doğrulayın.

---

## Seçenek B — n8n Cloud (`futbol_bulten_workflow_cloud.json`)

### Ortam değişkenleri

n8n Cloud'da **Settings → Variables** üzerinden (self-hosted'daki gibi
process env değil, n8n'in kendi arayüzünden tanımlanır):

| Değişken | Açıklama | Örnek |
|---|---|---|
| `AJAN_ORDUSU_API_URL` | API'nin adresi | `https://futbol-analiz-motoru.onrender.com` |
| `AJAN_ORDUSU_COMPETITION` | football-data.org lig kodu | `PL` |
| `AJAN_ORDUSU_SEASON` | API-Football sezon yılı | `2025` |
| `AJAN_ORDUSU_SPORT_KEY` | The Odds API lig anahtarı (opsiyonel) | `soccer_epl` |
| `AJAN_ORDUSU_SMTP_FROM` | Bültenin gönderileceği e-posta adresi (SMTP hesabınız) | `bulten@gmail.com` |
| `AJAN_ORDUSU_NOTIFY_EMAIL` | Bültenin ulaşacağı e-posta adresi | `siz@ornek.com` |

### SMTP kimlik bilgisi

"E-postayla Gönder" node'u bir SMTP kimlik bilgisi (credential) ister —
Gmail kullanıyorsanız normal şifreniz değil, bir **Uygulama Şifresi** (App
Password) gerekir: Google Hesabı → Güvenlik → 2 Adımlı Doğrulama (açık
olmalı) → Uygulama Şifreleri → yeni bir tane oluşturun. n8n'de **Credentials
→ New → SMTP** ekranından host (`smtp.gmail.com`), port (`587`), kullanıcı
adı ve bu uygulama şifresiyle "Ajan Ordusu SMTP" adında bir kimlik bilgisi
oluşturup workflow'daki node'a bağlayın.

### Import ve test

n8n arayüzünde: **Workflows → Import from File** → `futbol_bulten_workflow_cloud.json`.
SMTP kimlik bilgisini node'a bağladıktan sonra **Execute Workflow** ile
tetikleyip `AJAN_ORDUSU_NOTIFY_EMAIL` adresine bültenin ek dosya olarak
geldiğini doğrulayın.

---

## Ortak: Zamanlamayı değiştirmek

"Günlük Tetikleyici" node'undaki cron ifadesini (`0 8 * * *`) n8n
arayüzünden değiştirebilirsiniz — ör. haftalık bülten için `0 8 * * 1`
(her Pazartesi 08:00).

## İleride mesajlaşma kanalı eklemek

Her iki workflow'da da son node'dan sonra tek bir n8n node'u (Telegram,
Discord, ek bir Send Email) ekleyip `markdown` alanını (ya da `matches`
dizisini) ona bağlamanız yeterlidir — bu bilinçli olarak kapsam dışı
bırakıldı, istendiğinde küçük bir ekleme.
