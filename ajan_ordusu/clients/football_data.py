"""football-data.org v4 API için ince istemci.

Ücretsiz kayıtlı plan: dakikada 10 istek, çoğu büyük lig dahil (Süper Lig dahil).
Kayıt: https://www.football-data.org/client/register
Dokümantasyon: https://docs.football-data.org/general/v4/policies.html

Kullanım:
    client = FootballDataClient(token="...")
    matches = client.get_team_matches(team_id=524, limit=5)

Not (kota koruması): Bu istemci, aynı süreç (process) içindeki TÜM
çağrıları (farklı HTTP isteklerinden gelenler dahil) tek bir global
zamanlayıcıyla aralıklandırır — böylece art arda gelen birden fazla
kullanıcı isteği, ücretsiz planın dakika limitini birlikte aşmaz.
"""

import threading
import time
from typing import Any, Dict, List, Optional

import requests

from .. import config

BASE_URL = "https://api.football-data.org/v4"

# Bu, tek bir sürecin TÜM FootballDataClient çağrıları arasında paylaşılır
# (instance'a özel değil) — aksi hâlde ayrı ayrı HTTP isteklerinden gelen
# çağrılar birbirinden habersiz aynı anda hızlı istek atıp kotayı aşabilir.
_throttle_lock = threading.Lock()
_last_request_at = [0.0]


class FootballDataClientError(RuntimeError):
    pass


class FootballDataClient:
    def __init__(self, token: Optional[str] = None, timeout: float = 15.0):
        self.token = token or config.FOOTBALL_DATA_API_TOKEN
        if not self.token:
            raise FootballDataClientError(
                "FOOTBALL_DATA_API_TOKEN ortam değişkeni tanımlı değil. "
                "https://www.football-data.org/client/register adresinden "
                "ücretsiz bir anahtar alıp ortam değişkeni olarak ayarlayın."
            )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"X-Auth-Token": self.token})

    def _wait_for_quota(self) -> None:
        with _throttle_lock:
            remaining = config.FOOTBALL_DATA_REQUEST_DELAY_SECONDS - (time.monotonic() - _last_request_at[0])
            if remaining > 0:
                time.sleep(remaining)
            _last_request_at[0] = time.monotonic()

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self._wait_for_quota()
        response = self.session.get(f"{BASE_URL}{path}", params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_competition_teams(self, competition_code: str) -> List[Dict[str, Any]]:
        """Örn. competition_code='PL' (Premier League), 'TR1' (Süper Lig, kapsam değişebilir)."""
        return self._get(f"/competitions/{competition_code}/teams").get("teams", [])

    def get_competition_matches(
        self, competition_code: str, date_from: Optional[str] = None, date_to: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._get(f"/competitions/{competition_code}/matches", params=params).get("matches", [])

    def get_team_matches(
        self,
        team_id: int,
        status: str = "FINISHED",
        limit: int = 10,
        date_from: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Form Analiz Ajanı için: bir takımın geçmiş maçları (en yeni önce).

        `date_from` verilmezse API'nin dokümante edilmemiş varsayılan
        penceresine (genelde güncel sezon) güvenilir — bu, sezonun henüz
        yeni başladığı dönemlerde yanlışlıkla "hiç bitmiş maç yok" sonucu
        verebilir. Geçmişe dönük gerçek bir pencere garantilemek için
        çağıran taraf (main.py) açık bir `date_from` geçmelidir.
        """
        params: Dict[str, Any] = {"status": status, "limit": limit}
        if date_from:
            params["dateFrom"] = date_from
        data = self._get(f"/teams/{team_id}/matches", params=params)
        return data.get("matches", [])

    def get_head_to_head(self, match_id: int, limit: int = 10) -> Dict[str, Any]:
        """H2H Ajanı için: planlı/oynanmış bir maçın taraflarının geçmiş karşılaşmaları."""
        return self._get(f"/matches/{match_id}/head2head", params={"limit": limit})

    def get_competition_standings(self, competition_code: str) -> List[Dict[str, Any]]:
        """Puan Durumu Ajanı için: lig tablosu. TOTAL tipindeki tabloyu döndürür
        (HOME/AWAY ayrı tablolar da API'de mevcut ama burada kullanılmıyor)."""
        data = self._get(f"/competitions/{competition_code}/standings")
        for table in data.get("standings", []):
            if table.get("type") == "TOTAL":
                return table.get("table", [])
        return []
