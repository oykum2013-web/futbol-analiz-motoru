"""Ortam değişkenlerinden okunan yapılandırma.

Hiçbir API anahtarı kod içine gömülmez; her zaman ortam değişkeninden okunur.
"""

import os

FOOTBALL_DATA_API_TOKEN = os.environ.get("FOOTBALL_DATA_API_TOKEN")

# Form/H2H ajanlarının varsayılan olarak dikkate alacağı maç sayısı.
DEFAULT_FORM_MATCHES = 5
DEFAULT_H2H_MATCHES = 5
