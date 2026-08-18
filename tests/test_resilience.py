"""football-data.org kaynaklı hatalara (ör. 429 kota aşımı) karşı dayanıklılık testleri.

Gerçek bir kullanımda karşılaşılan bug'ın (bkz. main.py geçmişi) tekrar
etmediğini doğrular: tek bir takımın verisi alınamadığında tüm bülten
çökmemeli, "veri yok" olarak raporlanmalı.
"""

from unittest.mock import MagicMock

import requests

from ajan_ordusu.api import _upstream_error_response
from ajan_ordusu.main import _safe_get_team_matches


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
