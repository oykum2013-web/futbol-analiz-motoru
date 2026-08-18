"""Ortam değişkenlerinden okunan yapılandırma.

Hiçbir API anahtarı kod içine gömülmez; her zaman ortam değişkeninden okunur.
"""

import os

FOOTBALL_DATA_API_TOKEN = os.environ.get("FOOTBALL_DATA_API_TOKEN")
API_FOOTBALL_KEY = os.environ.get("API_FOOTBALL_KEY")
THE_ODDS_API_KEY = os.environ.get("THE_ODDS_API_KEY")

# Form/H2H ajanlarının varsayılan olarak dikkate alacağı maç sayısı.
DEFAULT_FORM_MATCHES = 5
DEFAULT_H2H_MATCHES = 5

# Sakatlık/Kadro Ajanı'nın etki skorunu ölçeklendirme katsayısı
# (bkz. agents/squad_analysis.py) — impact_score = min(1.0, katsayı * ağırlıklı eksik sayısı)
SQUAD_IMPACT_SCALE = 0.10

# Tahmin Ajanı'nda piyasa (oran) konsensüsünün model tahminiyle harmanlanma ağırlığı
# (bkz. agents/prediction.py) — 0.5 = eşit ağırlık.
MARKET_BLEND_WEIGHT = 0.5

# football-data.org ücretsiz plan dakikada 10 istekle sınırlıdır. Bülten modu
# birden çok maç için art arda istek attığından, istekler arasında bu kadar
# saniye beklenir (güvenlik payıyla ~9 istek/dk) — bkz. main.py _RateLimiter.
FOOTBALL_DATA_REQUEST_DELAY_SECONDS = 6.5
