"""football-data.org kaynaklı hatalara (ör. 429 kota aşımı) karşı dayanıklılık testleri.

Gerçek bir kullanımda karşılaşılan bug'ın (bkz. main.py geçmişi) tekrar
etmediğini doğrular: tek bir takımın verisi alınamadığında tüm bülten
çökmemeli, "veri yok" olarak raporlanmalı.
"""

from unittest.mock import MagicMock, patch

import requests

from ajan_ordusu.api import _upstream_error_response
from ajan_ordusu.main import _safe_get_team_matches, build_bulletin_live_reports


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


def _fixture(match_id: int, status: str, utc_date: str, home_id: int, away_id: int) -> dict:
    return {
        "id": match_id,
        "status": status,
        "utcDate": utc_date,
        "homeTeam": {"id": home_id, "name": f"Ev {home_id}"},
        "awayTeam": {"id": away_id, "name": f"Deplasman {away_id}"},
    }


@patch("ajan_ordusu.main.FootballDataClient")
def test_build_bulletin_live_reports_with_next_n_picks_earliest_scheduled_fixtures(mock_client_cls):
    client = MagicMock()
    mock_client_cls.return_value = client
    client.get_competition_standings.return_value = []
    client.get_team_matches.return_value = []
    client.get_competition_matches.return_value = [
        _fixture(3, "SCHEDULED", "2026-09-03T00:00:00Z", 30, 40),
        _fixture(1, "FINISHED", "2026-08-20T00:00:00Z", 10, 20),  # zaten oynanmış -> hariç tutulmalı
        _fixture(2, "SCHEDULED", "2026-08-25T00:00:00Z", 10, 20),
        _fixture(4, "TIMED", "2026-08-30T00:00:00Z", 50, 60),
    ]

    reports = build_bulletin_live_reports("PL", None, None, season=2025, next_n=2)

    # Bitmiş maç hariç tutulmalı, kalanlardan tarihe göre en erken 2 tanesi seçilmeli.
    assert len(reports) == 2
    assert reports[0].prediction.home.name == "Ev 10"
    assert reports[1].prediction.home.name == "Ev 50"
    # Puan durumu, maç başına değil lig başına TEK SEFERDE çekilmeli.
    client.get_competition_standings.assert_called_once_with("PL")
