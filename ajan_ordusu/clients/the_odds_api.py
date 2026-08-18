"""The Odds API (the-odds-api.com) için ince istemci.

Ücretsiz plan ayda 500 kredi ile sınırlıdır. Kotanın hızlı tükenmemesi için bu
istemci UTC gününe göre basit bir dosya önbelleği (cache) tutar: aynı gün
içinde aynı lig için tekrar çağrıldığında API'ye yeniden istek atmaz.

Önerilen kullanım: sık sık değil, GÜNDE BİR KEZ toplu çekim (ör. n8n/cron ile
günlük tetikleme) — bu istemcinin varsayılan davranışı (`use_cache=True`) zaten
bunu teşvik eder.

Kayıt: https://the-odds-api.com/ (Free plan, e-posta ile anahtar)
Dokümantasyon: https://the-odds-api.com/liveapi/guides/v4/
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from .. import config

BASE_URL = "https://api.the-odds-api.com/v4"
DEFAULT_CACHE_DIR = Path.home() / ".cache" / "ajan_ordusu" / "the_odds_api"


class TheOddsApiClientError(RuntimeError):
    pass


class TheOddsApiClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = 15.0,
        cache_dir: Optional[Path] = None,
    ):
        self.api_key = api_key or config.THE_ODDS_API_KEY
        if not self.api_key:
            raise TheOddsApiClientError(
                "THE_ODDS_API_KEY ortam değişkeni tanımlı değil. "
                "https://the-odds-api.com/ adresinden ücretsiz bir anahtar alıp "
                "ortam değişkeni olarak ayarlayın."
            )
        self.timeout = timeout
        self.session = requests.Session()
        self.cache_dir = cache_dir or DEFAULT_CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, sport_key: str) -> Path:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        return self.cache_dir / f"{sport_key}_{today}.json"

    def get_odds(
        self,
        sport_key: str,
        regions: str = "eu",
        markets: str = "h2h",
        use_cache: bool = True,
    ) -> List[Dict[str, Any]]:
        """Bir lig için güncel maç oranlarını döner.

        `use_cache=True` (varsayılan) iken aynı UTC günü içinde aynı lig için
        tekrar çağrıldığında API'ye yeniden istek atılmaz — kota israfını
        önlemek için günlük toplu çekim davranışı varsayılan olarak uygulanır.
        """
        cache_path = self._cache_path(sport_key)
        if use_cache and cache_path.exists():
            return json.loads(cache_path.read_text())

        response = self.session.get(
            f"{BASE_URL}/sports/{sport_key}/odds",
            params={
                "apiKey": self.api_key,
                "regions": regions,
                "markets": markets,
                "oddsFormat": "decimal",
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()

        if use_cache:
            cache_path.write_text(json.dumps(data))
        return data

    @staticmethod
    def find_event(
        events: List[Dict[str, Any]], home_team: str, away_team: str
    ) -> Optional[Dict[str, Any]]:
        """Takım adına göre (büyük/küçük harf duyarsız, tam eşleşme) maçı bulur.

        Bulunamazsa None döner — bu durumda çağıran taraf sahte oran
        UYDURMAMALI, "veri yok" olarak raporlamalıdır.
        """
        home_l, away_l = home_team.lower(), away_team.lower()
        for event in events:
            if event.get("home_team", "").lower() == home_l and event.get("away_team", "").lower() == away_l:
                return event
        return None
