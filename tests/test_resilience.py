"""football-data.org kaynaklı hatalara (ör. 429 kota aşımı) karşı dayanıklılık testleri.

Gerçek bir kullanımda karşılaşılan bug'ın (bkz. main.py geçmişi) tekrar
etmediğini doğrular: tek bir takımın verisi alınamadığında tüm bülten
çökmemeli, "veri yok" olarak raporlanmalı.
"""

from unittest.mock import MagicMock, patch

import requests

from ajan_ordusu.api import _upstream_error_response
from ajan_ordusu.clients.api_football import ApiFootballClient
from ajan_ordusu.main import _fetch_missing_players, _safe_get_team_matches


def test_safe_get_team_matches_returns_empty_list_on_http_error():
    client = MagicMock()
    client.get_team_matches.side_effect = requests.exceptions.HTTPError("429 Too Many Requests")

    result = _safe_get_team_matches(client, "524")

    assert result == []


def test_safe_get_team_matches_returns_data_on_success():
    client = MagicMock()
    client.get_team_matches.return_value = [{"id": 1}]

    result = _safe_get_team_matches(client, "524")

    assert result == [{"id": 1}]


def test_upstream_error_response_maps_429_to_429_with_clear_message():
    response = MagicMock()
    response.status_code = 429
    exc = requests.exceptions.HTTPError(response=response)

    http_exc = _upstream_error_response(exc)

    assert http_exc.status_code == 429
    assert "kota" in http_exc.detail.lower()


def test_upstream_error_response_maps_other_http_errors_to_502():
    response = MagicMock()
    response.status_code = 500
    exc = requests.exceptions.HTTPError(response=response)

    http_exc = _upstream_error_response(exc)

    assert http_exc.status_code == 502


# --- API-Football takım ID eşleştirme (bkz. proje geçmişi: football-data.org
# ve API-Football'un ID uzayları farklı, aynı sayı farklı kulüplere işaret
# edebilir — ör. football-data.org id=57 Arsenal iken API-Football id=57
# Ipswich'tir. Bu testler, yanlış takımın sakatlık verisinin ASLA sessizce
# gösterilmediğini doğrular.) ---


def test_find_team_id_returns_id_on_single_unambiguous_match():
    client = ApiFootballClient(api_key="test-key")
    with patch.object(client, "_get", return_value={"response": [{"team": {"id": 42, "name": "Arsenal"}}]}):
        assert client.find_team_id("Arsenal") == 42


def test_find_team_id_returns_none_when_multiple_clubs_share_a_name():
    client = ApiFootballClient(api_key="test-key")
    raw = {
        "response": [
            {"team": {"id": 42, "name": "Arsenal", "country": "England"}},
            {"team": {"id": 4403, "name": "Arsenal", "country": "Guadeloupe"}},
            {"team": {"id": 9419, "name": "Arsenal", "country": "Belarus"}},
        ]
    }
    with patch.object(client, "_get", return_value=raw):
        assert client.find_team_id("Arsenal") is None


def test_find_team_id_disambiguates_with_country_filter():
    client = ApiFootballClient(api_key="test-key")
    raw = {
        "response": [
            {"team": {"id": 42, "name": "Arsenal", "country": "England"}},
            {"team": {"id": 4403, "name": "Arsenal", "country": "Guadeloupe"}},
        ]
    }
    with patch.object(client, "_get", return_value=raw):
        assert client.find_team_id("Arsenal", country="England") == 42


def test_fetch_missing_players_returns_none_and_never_queries_injuries_when_id_ambiguous():
    """Kritik: takım ID'si çözülemiyorsa, YANLIŞ bir takımın sakatlık verisini
    göstermek yerine sorgu hiç yapılmamalı — sessizce yanlış veri göstermek,
    'veri yok' demekten çok daha kötüdür (bkz. proje veri bütünlüğü kuralı)."""
    with patch("ajan_ordusu.main.ApiFootballClient") as MockClient:
        instance = MockClient.return_value
        instance.find_team_id.return_value = None

        result = _fetch_missing_players("57", "Arsenal", season=2026)

        assert result is None
        instance.get_team_injuries.assert_not_called()


def test_fetch_missing_players_uses_resolved_id_not_football_data_id():
    """football-data.org id'si (57) API-Football'a asla doğrudan gönderilmemeli —
    yalnızca isimden çözülen gerçek API-Football id'si (42) kullanılmalı."""
    with patch("ajan_ordusu.main.ApiFootballClient") as MockClient:
        instance = MockClient.return_value
        instance.find_team_id.return_value = 42
        instance.get_team_injuries.return_value = []

        _fetch_missing_players("57", "Arsenal", season=2026)

        instance.get_team_injuries.assert_called_once_with(42, 2026)
