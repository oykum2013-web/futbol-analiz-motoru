"""HTTP API sarmalayıcı — n8n gibi orkestrasyon araçlarının Cron + HTTP Request
node'uyla bülten/tahmin pipeline'ını tetikleyebilmesi için.

Bu modül alttaki ajanların üzerine ince bir HTTP katmanıdır: hiçbir veri
üretmez, sadece `main.py`'deki aynı fonksiyonları çağırıp JSON olarak döner.
Veri bütünlüğü kuralı burada da geçerlidir — gerçek veri bulunamadığında
sahte bir sayı üretmek yerine ilgili ajanın ürettiği "VERİ YOK"/"Yetersiz
Veri" durumu JSON'a olduğu gibi yansır (bkz. schemas.py, agents/bulletin.py).

Çalıştırma:
    pip install -r requirements.txt
    uvicorn ajan_ordusu.api:app --host 0.0.0.0 --port 8000

Uç noktalar:
    GET /health
    GET /teams?competition=PL                    — gerçek takım ID'lerini bulmak için
    GET /bulletin/demo                          — ağ/anahtar gerektirmez
    GET /bulletin?competition=PL&date_from=...&date_to=...&season=...&sport_key=...
    GET /match?home_team_id=...&away_team_id=...&home_name=...&away_name=...&season=...&sport_key=...
"""

from typing import Optional

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import main as pipeline
from .agents.bulletin import to_bulletin_dict
from .clients.api_football import ApiFootballClientError
from .clients.football_data import FootballDataClientError
from .clients.the_odds_api import TheOddsApiClientError

app = FastAPI(
    title="Futbol Analiz Motoru — Ajan Ordusu API",
    description="n8n gibi orkestrasyon araçları için bülten/tahmin pipeline'ının HTTP sarmalayıcısı.",
    version="0.1.0",
)

# Tüm uç noktalar herkese açık, okuma amaçlı ve kimlik doğrulama gerektirmiyor
# (hassas veri/oturum yok) — mobil uygulamanın web hedefi ve tarayıcıdan
# yapılan geliştirme testleri için CORS'u herkese açık bırakmak güvenli.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Yapılandırma eksikliğinden (API anahtarı yok) kaynaklanan hatalar 400 (istemci
# düzeltebilir); gerçek bir veri kaynağı hatası ise 502/429 (yukarı akış sorunu) döner.
_CONFIG_ERRORS = (FootballDataClientError, ApiFootballClientError, TheOddsApiClientError)


def _upstream_error_response(exc: Exception) -> HTTPException:
    """Bir veri kaynağı (football-data.org vb.) isteği başarısız olduğunda,
    500 ile çökmek yerine anlaşılır bir hata döner — sahte veri üretmek yerine
    ne olduğunu açıkça söyler.
    """
    if isinstance(exc, requests.exceptions.HTTPError) and exc.response is not None:
        status = exc.response.status_code
        if status == 429:
            return HTTPException(
                status_code=429,
                detail=(
                    "football-data.org kota limiti aşıldı (ücretsiz plan: dakikada 10 istek). "
                    "Birkaç dakika bekleyip tekrar deneyin."
                ),
            )
        return HTTPException(status_code=502, detail=f"football-data.org kaynağından hata alındı (HTTP {status}).")
    return HTTPException(status_code=502, detail=f"Veri kaynağına ulaşılamadı: {exc}")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/teams")
def teams(
    competition: str = Query(..., description="football-data.org lig kodu (ör. PL, BL1, PD, SA, FL1)")
) -> dict:
    """Bir ligdeki gerçek takımları ve football-data.org ID'lerini döner —
    /match ve /bulletin çağrılarında hangi team_id'nin kullanılacağını
    bulmak için (ID'ler tahmin edilmemeli, buradan doğrulanmalı)."""
    try:
        client = pipeline.FootballDataClient()
        raw_teams = client.get_competition_teams(competition)
    except _CONFIG_ERRORS as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.exceptions.RequestException as exc:
        raise _upstream_error_response(exc) from exc

    return {
        "competition": competition,
        "teams": [{"id": t.get("id"), "name": t.get("name"), "short_name": t.get("shortName")} for t in raw_teams],
    }


@app.get("/debug/team-matches")
def debug_team_matches(
    team_id: int = Query(..., description="football-data.org takım ID'si"),
    status: str = Query("FINISHED"),
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
) -> dict:
    """Teşhis amaçlı: bir takım için football-data.org'un HAM yanıtını,
    hiçbir ajan/analiz katmanından geçirmeden, tek bir hızlı istekle döner.
    """
    try:
        client = pipeline.FootballDataClient()
        raw = client.get_team_matches(team_id, status=status, limit=10, date_from=date_from)
    except _CONFIG_ERRORS as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.exceptions.RequestException as exc:
        raise _upstream_error_response(exc) from exc

    return {"team_id": team_id, "status": status, "date_from": date_from, "match_count": len(raw), "raw": raw[:3]}


@app.get("/bulletin/demo")
def bulletin_demo() -> dict:
    """Ağ/anahtar gerektirmeyen, kurgusal iki maçlık örnek bülten (JSON)."""
    reports = pipeline.build_demo_bulletin_reports()
    data = to_bulletin_dict(reports, title="Günlük Tahmin Bülteni (DEMO)")
    data["demo"] = True
    data["demo_warning"] = (
        "Bu bir demo yanıtıdır — takım adları ve tüm veriler tamamen kurgusaldır, "
        "gerçek bir maçı ya da takımı temsil etmez."
    )
    return data


@app.get("/bulletin")
def bulletin(
    competition: str = Query(..., description="football-data.org lig kodu (ör. PL, BL1)"),
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
    season: int = Query(2025, description="API-Football sakatlık sorgusu için sezon yılı"),
    sport_key: Optional[str] = Query(
        None, description="The Odds API lig anahtarı (ör. soccer_epl) — verilmezse oran verisi atlanır"
    ),
) -> dict:
    try:
        reports = pipeline.build_bulletin_live_reports(competition, date_from, date_to, season, sport_key)
    except _CONFIG_ERRORS as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.exceptions.RequestException as exc:
        raise _upstream_error_response(exc) from exc

    title = f"{date_from} – {date_to} Tahmin Bülteni ({competition})"
    return to_bulletin_dict(reports, title=title)


@app.get("/match")
def match(
    home_team_id: str = Query(..., description="football-data.org ev sahibi takım ID'si"),
    away_team_id: str = Query(..., description="football-data.org deplasman takım ID'si"),
    home_name: str = Query("Ev Sahibi"),
    away_name: str = Query("Deplasman"),
    season: int = Query(2025, description="API-Football sakatlık sorgusu için sezon yılı"),
    sport_key: Optional[str] = Query(None, description="The Odds API lig anahtarı"),
    competition: Optional[str] = Query(
        None,
        description=(
            "football-data.org lig kodu (ör. PL, BL1) — API-Football takım "
            "ID'sini isimden çözerken ülkeye göre tekilleştirmek için kullanılır "
            "(aynı isimli birden çok kulüp varsa yanlış takımın sakatlık "
            "verisini göstermemek için)."
        ),
    ),
) -> dict:
    try:
        client = pipeline.FootballDataClient()
        report = pipeline._analyze_live_match(
            client, home_team_id, away_team_id, home_name, away_name, season, sport_key,
            competition_code=competition,
        )
    except _CONFIG_ERRORS as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except requests.exceptions.RequestException as exc:
        raise _upstream_error_response(exc) from exc

    return to_bulletin_dict([report], title=f"{home_name} vs {away_name}")
