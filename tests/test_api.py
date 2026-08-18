from fastapi.testclient import TestClient

from ajan_ordusu.api import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_bulletin_demo_returns_structured_data_and_markdown():
    r = client.get("/bulletin/demo")
    assert r.status_code == 200
    data = r.json()

    assert data["demo"] is True
    assert data["match_count"] == 2
    assert "RİSK UYARISI" in data["risk_warning"]
    assert "RİSK UYARISI" in data["markdown"]

    # İkinci demo maçı kasıtlı olarak verisiz -> API de bunu gizlememeli.
    second = data["matches"][1]
    assert second["prediction"]["confidence"] == "Yetersiz Veri"
    assert len(second["data_gaps"]) > 0


def test_bulletin_live_without_token_returns_400_not_fake_data():
    r = client.get("/bulletin", params={"competition": "PL", "date_from": "2026-08-18", "date_to": "2026-08-18"})
    assert r.status_code == 400
    assert "FOOTBALL_DATA_API_TOKEN" in r.json()["detail"]


def test_match_live_without_token_returns_400_not_fake_data():
    r = client.get("/match", params={"home_team_id": "1", "away_team_id": "2"})
    assert r.status_code == 400
    assert "FOOTBALL_DATA_API_TOKEN" in r.json()["detail"]
