# Futbol Analiz Motoru — Mobil Uygulama

Expo/React Native (TypeScript) mobil uygulaması. `ajan_ordusu/api.py`
(FastAPI) sunucusuna bağlanır; kendi başına veri üretmez.

## Çalıştırma

```bash
cd mobile
npm install
npx expo start          # QR kod / simülatör
npx expo start --web    # tarayıcıda dene
npm test                # Jest test paketi (api/client.ts, MatchCard renk haritası)
```

## Backend'e bağlanma

1. Repo kökünde `.env` dosyasını doldurun (bkz. `.env.example`):
   ```bash
   export FOOTBALL_DATA_API_TOKEN=...   # https://www.football-data.org/client/register
   ```
2. Backend'i başlatın:
   ```bash
   uvicorn ajan_ordusu.api:app --host 0.0.0.0 --port 8000
   ```
3. Uygulama içinde sağ üstteki ⚙️ ikonundan "API Adresi"ni ayarlayın:
   - Web/simülatörden test ediyorsanız: `http://localhost:8000`
   - Fiziksel bir telefondan test ediyorsanız: bilgisayarınızın LAN IP'si,
     ör. `http://192.168.1.23:8000` (telefon ve bilgisayar aynı ağda olmalı)

`/bulletin/demo` anahtar gerektirmez; gerçek maç sorgusu (`/match`) için
sunucuda `FOOTBALL_DATA_API_TOKEN` tanımlı olmalı.

## Mevcut ekranlar

- **Onboarding** (`src/screens/OnboardingScreen.tsx`) — bahis tavsiyesi
  vermediği, olasılık tabanlı olduğu ve 18+ olduğu kabul edilmeden
  geçilemeyen zorunlu ekran (`src/constants/legal.ts`).
- **Tahmin ekranı** (`src/screens/PredictionScreen.tsx`):
  - Açılışta `/bulletin/demo` — sınırsız, açıkça DEMO etiketli.
  - "Gerçek Maç Sorgula": lig seçip (`TeamPicker`, `/teams` uç noktası)
    Ev Sahibi/Deplasman takımı seçerek `/match` sorgulanır; listede
    olmayan takımlar için elle ID girişi de var.
- **Paywall** (`src/screens/PaywallScreen.tsx`) — ücretsiz plan günde 1
  gerçek maç sorgusuyla sınırlı (`src/state/dailyUsage.ts`); limit
  dolunca veya "Yükselt"e basılınca açılır.

## Veri bütünlüğü / şeffaflık kuralı bu ekranlarda nasıl uygulanıyor

Güven rozeti ve eksik-veri uyarısı (`data_gaps`) **her zaman** gösterilir —
ücretsiz/premium fark etmez. Paywall yalnızca detaylı gerekçeyi
(form/H2H/kadro/piyasa kırılımı) kilitler. Bu bilinçli bir tercih: bir
kullanıcıyı "veri yetersiz" uyarısından mahrum bırakmak, onu yanıltıp
güven/hukuki risk yaratır (bkz. proje kök `CLAUDE.md`).

## Bilinen sınırlar / yapılacaklar

- **Ödeme gerçek değil.** `src/state/subscription.ts`'deki `purchase()`
  yalnızca cihazda yerel bir bayrağı işaretleyen bir TEST akışı — ücret
  tahsil etmez. Gerçek abonelik için Apple/Google'ın uygulama içi satın
  alma sistemleri zorunlu (harici bir ödeme sayfası politika ihlali
  sayılır); pratikte RevenueCat + StoreKit/Play Billing entegrasyonu
  gerekiyor. Bunun için App Store Connect / Google Play Console
  geliştirici hesapları gerekli — henüz kurulmadı.
- **Gerçek veriyle uçtan uca canlı test henüz yapılmadı.** Bu ortamdan
  (otonom oturum) gerçek `FOOTBALL_DATA_API_TOKEN`'ı canlı ağda
  kullanmak güvenlik sınıflandırıcısı tarafından engellendi — bu
  kasıtlı bir koruma (bir ajanın gerçek/kotalı bir anahtarı sizin
  onayınız olmadan harcamasını önlemek için). Token `.env`'e kaydedildi
  (git'e girmiyor); ilk canlı testi siz kendi makinenizde/sunucunuzda
  `uvicorn`'u çalıştırıp uygulamayı ona bağlayarak yapabilirsiniz — kod
  tarafı demo ve mocklanmış senaryolarla uçtan uca doğrulandı.
- Premium bayrağı sadece cihazda tutuluyor; gerçek bir hesap/backend
  doğrulaması yok (bir kullanıcı local storage'ı silip/değiştirip
  Premium'u taklit edebilir) — bu, mock aşamasında beklenen bir durum,
  gerçek IAP entegrasyonuyla (makbuz doğrulama) çözülür.
