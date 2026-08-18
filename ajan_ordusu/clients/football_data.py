"""football-data.org v4 API için ince istemci.

Ücretsiz kayıtlı plan: dakikada 10 istek, çoğu büyük lig dahil (Süper Lig dahil).
Kayıt: https://www.football-data.org/client/register
Dokümantasyon: https://docs.football-data.org/general/v4/policies.html

Kullanım:
    client = FootballDataClient(token="...")
    matches = client.get_team_matches(team_id=524, limit=5)
"""

from typing import Any, Dict, List, Optional

import requests

from .. import config

BASE_URL = "https://api.football-data.org/v4"


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

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        self, team_id: int, status: str = "FINISHED", limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Form Analiz Ajanı için: bir takımın geçmiş maçları (en yeni önce)."""
        data = self._get(f"/teams/{team_id}/matches", params={"status": status, "limit": limit})
        return data.get("matches", [])

    def get_head_to_head(self, match_id: int, limit: int = 10) -> Dict[str, Any]:
        """H2H Ajanı için: planlı/oynanmış bir maçın taraflarının geçmiş karşılaşmaları."""
        return self._get(f"/matches/{match_id}/head2head", params={"limit": limit})
