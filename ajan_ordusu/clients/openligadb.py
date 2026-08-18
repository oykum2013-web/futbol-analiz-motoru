"""OpenLigaDB API için ince istemci (anahtar gerekmez, ücretsiz).

Ağırlıklı olarak Almanya ligleri (Bundesliga, 2. Bundesliga, 3. Liga, DFB Pokal)
ve bazı ek ligleri kapsar. Türkiye Süper Lig kapsamı doğrulanmalıdır.
Dokümantasyon: https://www.openligadb.de/

Not: OpenLigaDB'de takıma özel "son N maç" veya "head-to-head" için ayrı bir
endpoint garantisi yoktur; bu istemci sezon bazlı maç verisini çeker,
takıma/eşleşmeye göre filtreleme işini çağıran koda (data_collection ajanı) bırakır.
"""

from typing import Any, Dict, List, Optional

import requests

BASE_URL = "https://api.openligadb.de"


class OpenLigaDBClient:
    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout
        self.session = requests.Session()

    def _get(self, path: str) -> Any:
        response = self.session.get(f"{BASE_URL}{path}", timeout=self.timeout)
        response.raise_for_status()
        return response.json()

    def get_season_matches(self, league_shortcut: str, season: str) -> List[Dict[str, Any]]:
        """Örn. league_shortcut='bl1' (Bundesliga), season='2025'."""
        return self._get(f"/getmatchdata/{league_shortcut}/{season}")

    def get_current_matches(self, league_shortcut: str) -> List[Dict[str, Any]]:
        return self._get(f"/getmatchdata/{league_shortcut}")

    def get_table(self, league_shortcut: str, season: str) -> List[Dict[str, Any]]:
        return self._get(f"/getbltable/{league_shortcut}/{season}")

    def get_teams(self, league_shortcut: str, season: str) -> List[Dict[str, Any]]:
        return self._get(f"/getteamsbyleagueshortcut/{league_shortcut}/{season}")
