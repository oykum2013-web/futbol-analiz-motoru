"""football-data.org v4'ün iki ayrı, canlı API'ye karşı doğrulanmış kısıtını test eder:
1. `dateFrom` tek başına gönderilemez, `dateTo` ile eşleşmesi zorunlu (400 aksi hâlde).
2. `limit`, `dateFrom`/`dateTo` ile birlikte kabul edilmiyor (400).
Bu dosya, istemcinin bu iki kuralı da doğru uyguladığını ve `date_from` verildiğinde
en yeni `limit` maça doğru şekilde kırptığını doğrular. Gerçek bir HTTP isteği atmaz
(session.get mock'lanır)."""

from datetime import date

from ajan_ordusu.clients.football_data import FootballDataClient


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _make_client(monkeypatch, matches):
    client = FootballDataClient(token="fake-token")
    captured = {}

    def fake_get(url, params=None, timeout=None):
        captured["params"] = params
        return _FakeResponse({"matches": matches})

    monkeypatch.setattr(client.session, "get", fake_get)
    monkeypatch.setattr(
        "ajan_ordusu.clients.football_data.time.sleep", lambda *_: None
    )  # kota bekleme testte gereksiz
    return client, captured


def test_get_team_matches_never_sends_limit_with_date_from(monkeypatch):
    client, captured = _make_client(monkeypatch, matches=[{"id": i} for i in range(20)])

    client.get_team_matches(524, status="FINISHED", limit=5, date_from="2025-08-18")

    assert "limit" not in captured["params"]
    assert captured["params"]["dateFrom"] == "2025-08-18"


def test_get_team_matches_always_pairs_date_from_with_date_to(monkeypatch):
    client, captured = _make_client(monkeypatch, matches=[])

    client.get_team_matches(524, date_from="2025-08-18")

    assert captured["params"]["dateTo"] == date.today().isoformat()


def test_get_team_matches_respects_explicit_date_to(monkeypatch):
    client, captured = _make_client(monkeypatch, matches=[])

    client.get_team_matches(524, date_from="2025-08-18", date_to="2025-12-31")

    assert captured["params"]["dateTo"] == "2025-12-31"


def test_get_team_matches_trims_to_newest_n_when_date_from_given(monkeypatch):
    # API eskiden yeniye döner varsayımıyla: id küçük = eski, id büyük = yeni.
    raw_matches = [{"id": i} for i in range(20)]
    client, _ = _make_client(monkeypatch, matches=raw_matches)

    result = client.get_team_matches(524, limit=5, date_from="2025-08-18")

    assert [m["id"] for m in result] == [15, 16, 17, 18, 19]


def test_get_team_matches_sends_limit_when_no_date_from(monkeypatch):
    client, captured = _make_client(monkeypatch, matches=[{"id": 1}])

    client.get_team_matches(524, status="FINISHED", limit=7)

    assert captured["params"]["limit"] == 7
    assert "dateFrom" not in captured["params"]
