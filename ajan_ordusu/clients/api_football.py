"""API-Football (api-football.com) için ince istemci.

Sakatlık/Kadro Ajanı'nın kullandığı `/injuries` uç noktası ücretsiz planda
mevcuttur, ancak plan günde 100 istekle sınırlıdır ve genelde yalnızca
güncel sezona erişim verir.

Kayıt: https://www.api-football.com/pricing (Free plan)
Dokümantasyon: https://www.api-football.com/documentation-v3

Not: Aynı API RapidAPI üzerinden de sunulur; bu istemci doğrudan
api-football.com uç noktasını (x-apisports-key başlığı) kullanır.
"""

from typing import Any, Dict, List, Optional

import requests

from .. import config

BASE_URL = "https://v3.football.api-sports.io"


class ApiFootballClientError(RuntimeError):
    pass


class ApiFootballClient:
    def __init__(self, api_key: Optional[str] = None, timeout: float = 15.0):
        self.api_key = api_key or config.API_FOOTBALL_KEY
        if not self.api_key:
            raise ApiFootballClientError(
                "API_FOOTBALL_KEY ortam değişkeni tanımlı değil. "
                "https://www.api-football.com/pricing adresinden ücretsiz bir "
                "anahtar alıp ortam değişkeni olarak ayarlayın."
            )
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"x-apisports-key": self.api_key})

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = self.session.get(f"{BASE_URL}{path}", params=params, timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_team_injuries(self, team_id: int, season: int) -> List[Dict[str, Any]]:
        """Bir takımın belirli sezondaki güncel sakatlık/eksik oyuncu listesi.

        DİKKAT: `team_id` burada API-Football'un KENDİ takım ID sistemine göre
        olmalı — football-data.org'un ID'siyle KARIŞTIRILMAMALI. İki sağlayıcının
        ID'leri farklı ve örtüşen sayılar tamamen farklı takımlara işaret
        edebilir (ör. football-data.org'da 57 = Arsenal iken API-Football'da
        57 = Ipswich). Doğru ID `find_team_id` ile takım adından çözülmeli.
        """
        data = self._get("/injuries", params={"team": team_id, "season": season})
        return data.get("response", [])

    def find_team_id(self, team_name: str, country: Optional[str] = None) -> Optional[int]:
        """Takım adından API-Football'un kendi takım ID'sini bulur.

        football-data.org'dan gelen sayısal takım ID'leri API-Football'un
        ID sistemiyle ÖRTÜŞMEZ (iki farklı sağlayıcı, iki farklı ID uzayı) —
        bu yüzden sakatlık sorgusundan önce isim üzerinden gerçek ID'yi burada
        çözüyoruz. Aynı isimde birden fazla takım varsa (ör. dünyada birçok
        "Arsenal" kulübü var) ve `country` ile tekilleştirilemiyorsa, yanlış
        takımın verisini göstermemek için None döner — çağıran taraf bunu
        "veri yok" olarak raporlamalı, asla bir tahminle devam etmemeli.
        """
        params: Dict[str, Any] = {"name": team_name}
        if country:
            params["country"] = country
        data = self._get("/teams", params=params)
        results = data.get("response", [])
        if country:
            results = [r for r in results if (r.get("team") or {}).get("country") == country]
        if len(results) != 1:
            return None
        return (results[0].get("team") or {}).get("id")
