"""CLI giriş noktası: tek bir maç ya da çoklu maç bülteni için uçtan uca
analiz/tahmin üretir.

Kullanım:
    # Ağ/anahtar gerektirmeyen demo mod (örnek/kurgusal veriyle pipeline testi):
    python -m ajan_ordusu.main --demo
    python -m ajan_ordusu.main --bulletin-demo

    # Gerçek veri ile tek maç (football-data.org, FOOTBALL_DATA_API_TOKEN gerektirir):
    python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61

    # Sakatlık/kadro + oran verisi de dahil etmek için:
    #   API_FOOTBALL_KEY (sakatlık) ve THE_ODDS_API_KEY (oran) ortam değişkenleri tanımlı olmalı.
    python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --season 2025 \
        --sport-key soccer_epl

    # Gerçek veri ile günlük/haftalık bülten (bir lig + tarih aralığındaki tüm maçlar):
    python -m ajan_ordusu.main --bulletin --competition PL \
        --date-from 2026-08-18 --date-to 2026-08-18
"""

import argparse
import logging
import sys
from datetime import date, timedelta
from typing import Optional

import requests

from .agents.bulletin import format_bulletin_markdown
from .agents.data_collection import (
    filter_h2h_matches,
    filter_team_matches,
    normalize_football_data_matches,
)
from .agents.market_analysis import normalize_the_odds_api_event
from .agents.orchestrator import MatchAnalysisReport, format_report_markdown, run_pipeline
from .agents.squad_analysis import normalize_api_football_injuries
from .clients.api_football import ApiFootballClient, ApiFootballClientError
from .clients.football_data import FootballDataClient
from .clients.the_odds_api import TheOddsApiClient, TheOddsApiClientError
from .schemas import TeamRef

logger = logging.getLogger(__name__)

DEMO_BANNER = (
    "⚠️⚠️ BU BİR DEMO RAPORUDUR — takım adları ve tüm veriler tamamen "
    "KURGUSALDIR, gerçek bir maçı ya da takımı temsil etmez. Sadece "
    "pipeline'ı ağ/API anahtarı olmadan test etmek içindir. ⚠️⚠️\n"
)


def build_demo_report() -> MatchAnalysisReport:
    from .sample_data.demo_match import (
        H2H_MACLAR,
        TAKIM_A,
        TAKIM_A_EKSIKLER,
        TAKIM_A_ORANLAR,
        TAKIM_A_SON_MACLAR,
        TAKIM_B,
        TAKIM_B_EKSIKLER,
        TAKIM_B_SON_MACLAR,
    )

    return run_pipeline(
        TAKIM_A,
        TAKIM_B,
        TAKIM_A_SON_MACLAR,
        TAKIM_B_SON_MACLAR,
        H2H_MACLAR,
        TAKIM_A_EKSIKLER,
        TAKIM_B_EKSIKLER,
        TAKIM_A_ORANLAR,
    )


def run_demo() -> str:
    return DEMO_BANNER + format_report_markdown(build_demo_report())


def build_demo_bulletin_reports() -> list:
    """Birden fazla (kurgusal) maçla bülten çıktısını gösterir.

    İkinci maç bilinçli olarak veri eksikliği (form/H2H/kadro/oran yok)
    içerecek şekilde kurgulanmıştır — bültenin "VERİ YOK"/"Yetersiz Veri"
    uyarılarını gerçekten gösterdiğini kanıtlamak içindir.
    """
    from .sample_data.demo_match import TAKIM_C, TAKIM_D

    match1 = build_demo_report()
    # Kasıtlı olarak veri eksikliğini göstermek için: hiç maç/kadro/oran verisi verilmiyor.
    match2 = run_pipeline(TAKIM_C, TAKIM_D, [], [], [])
    return [match1, match2]


def run_bulletin_demo() -> str:
    bulletin = format_bulletin_markdown(build_demo_bulletin_reports(), title="Günlük Tahmin Bülteni (DEMO)")
    return DEMO_BANNER + bulletin


def _fetch_missing_players(team_id: str, season: int):
    """API_FOOTBALL_KEY tanımlıysa sakatlık/kadro verisini çeker; yoksa sessizce atlar (None)."""
    try:
        client = ApiFootballClient()
    except ApiFootballClientError:
        return None
    raw = client.get_team_injuries(int(team_id), season)
    return normalize_api_football_injuries(raw)


def _fetch_odds_quotes(sport_key: str, home_name: str, away_name: str):
    """THE_ODDS_API_KEY tanımlıysa oran verisini çeker; yoksa ya da maç bulunamazsa None döner.

    Kotayı korumak için istemci varsayılan olarak günlük (UTC) dosya önbelleği
    kullanır — aynı gün içinde aynı lig için tekrar çağrılırsa API'ye yeniden
    istek atılmaz.
    """
    try:
        client = TheOddsApiClient()
    except TheOddsApiClientError:
        return None
    events = client.get_odds(sport_key)
    event = client.find_event(events, home_name, away_name)
    if event is None:
        return None
    return normalize_the_odds_api_event(event)


def _safe_get_team_matches(client: FootballDataClient, team_id: str) -> list:
    """Bir takımın maç geçmişini çeker; kaynak hatası (ör. 429 kota aşımı,
    ağ hatası) durumunda çökmek yerine boş liste döner — bu, form/H2H
    ajanlarında zaten "veri yok" olarak doğru şekilde raporlanır (bkz. veri
    bütünlüğü kuralı: eksik veri sessizce uydurulmaz, ama tek bir maçın
    verisi alınamadı diye TÜM bülten de çökertilmez).

    Hata yutulmuyor — teşhis edilebilmesi için loglanıyor (bkz. sunucu logları).

    API'nin dokümante edilmemiş varsayılan tarih penceresine güvenmemek için
    (sezon henüz yeni başlamışken yanlışlıkla "hiç maç yok" sonucu
    verebiliyordu — bkz. proje geçmişi), açıkça son 365 günü istiyoruz.
    """
    date_from = (date.today() - timedelta(days=365)).isoformat()
    try:
        return client.get_team_matches(int(team_id), status="FINISHED", limit=10, date_from=date_from)
    except requests.exceptions.RequestException as exc:
        logger.warning("Takım %s için maç verisi çekilemedi: %s", team_id, exc)
        return []


def _analyze_live_match(
    client: FootballDataClient,
    home_team_id: str,
    away_team_id: str,
    home_name: str,
    away_name: str,
    season: int,
    sport_key: Optional[str] = None,
) -> MatchAnalysisReport:
    home_team = TeamRef(id=home_team_id, name=home_name)
    away_team = TeamRef(id=away_team_id, name=away_name)

    home_raw = _safe_get_team_matches(client, home_team_id)
    away_raw = _safe_get_team_matches(client, away_team_id)

    home_matches = filter_team_matches(normalize_football_data_matches(home_raw), home_team_id)
    away_matches = filter_team_matches(normalize_football_data_matches(away_raw), away_team_id)
    # H2H: iki takımın maç listelerinin birleşiminden ortak karşılaşmaları çıkar.
    h2h_matches = filter_h2h_matches(home_matches + away_matches, home_team_id, away_team_id)

    home_missing = _fetch_missing_players(home_team_id, season)
    away_missing = _fetch_missing_players(away_team_id, season)
    odds_quotes = _fetch_odds_quotes(sport_key, home_name, away_name) if sport_key else None

    return run_pipeline(
        home_team,
        away_team,
        home_matches,
        away_matches,
        h2h_matches,
        home_missing,
        away_missing,
        odds_quotes,
    )


def run_live(
    home_team_id: str,
    away_team_id: str,
    home_name: str,
    away_name: str,
    season: int,
    sport_key: Optional[str] = None,
) -> str:
    client = FootballDataClient()
    report = _analyze_live_match(client, home_team_id, away_team_id, home_name, away_name, season, sport_key)
    return format_report_markdown(report)


def build_bulletin_live_reports(
    competition_code: str,
    date_from: str,
    date_to: str,
    season: int,
    sport_key: Optional[str] = None,
) -> list:
    """Bir lig + tarih aralığındaki tüm maçlar için analiz raporlarını üretir.

    football-data.org'un dakika başı istek limitini korumak için istekler
    arasında otomatik yavaşlatma, istemcinin kendisi tarafından (tüm süreç
    genelinde paylaşılan şekilde) uygulanır — bkz. clients/football_data.py.
    """
    client = FootballDataClient()
    fixtures = client.get_competition_matches(competition_code, date_from=date_from, date_to=date_to)

    reports = []
    for fixture in fixtures:
        home = fixture.get("homeTeam") or {}
        away = fixture.get("awayTeam") or {}
        home_id, away_id = home.get("id"), away.get("id")
        if home_id is None or away_id is None:
            continue
        report = _analyze_live_match(
            client,
            str(home_id),
            str(away_id),
            home.get("name") or "?",
            away.get("name") or "?",
            season,
            sport_key,
        )
        reports.append(report)
    return reports


def run_bulletin_live(
    competition_code: str,
    date_from: str,
    date_to: str,
    season: int,
    sport_key: Optional[str] = None,
) -> str:
    reports = build_bulletin_live_reports(competition_code, date_from, date_to, season, sport_key)
    title = f"{date_from} – {date_to} Tahmin Bülteni ({competition_code})"
    return format_bulletin_markdown(reports, title=title)


def main() -> None:
    parser = argparse.ArgumentParser(description="Ajan ordusu analiz/tahmin/bülten pipeline'ı")
    parser.add_argument("--demo", action="store_true", help="Ağ/anahtar gerektirmeyen tek maç örneği")
    parser.add_argument(
        "--bulletin-demo", action="store_true", help="Ağ/anahtar gerektirmeyen çok maçlı bülten örneği"
    )
    parser.add_argument("--bulletin", action="store_true", help="Gerçek veriyle çok maçlı bülten üret")
    parser.add_argument("--competition", help="--bulletin için football-data.org lig kodu (ör. PL, BL1)")
    parser.add_argument("--date-from", help="--bulletin için başlangıç tarihi (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="--bulletin için bitiş tarihi (YYYY-MM-DD)")
    parser.add_argument("--home-team-id", help="football-data.org ev sahibi takım ID'si")
    parser.add_argument("--away-team-id", help="football-data.org deplasman takım ID'si")
    parser.add_argument("--home-name", default="Ev Sahibi", help="Raporda gösterilecek ev sahibi adı")
    parser.add_argument("--away-name", default="Deplasman", help="Raporda gösterilecek deplasman adı")
    parser.add_argument(
        "--season",
        type=int,
        default=2025,
        help="API-Football sakatlık sorgusu için sezon yılı (API_FOOTBALL_KEY tanımlıysa kullanılır)",
    )
    parser.add_argument(
        "--sport-key",
        help=(
            "The Odds API lig anahtarı (ör. soccer_epl, soccer_germany_bundesliga1) — "
            "THE_ODDS_API_KEY tanımlıysa oran verisini çekmek için kullanılır"
        ),
    )
    args = parser.parse_args()

    if args.demo:
        print(run_demo())
        return

    if args.bulletin_demo:
        print(run_bulletin_demo())
        return

    try:
        if args.bulletin:
            if not args.competition or not args.date_from or not args.date_to:
                parser.error("--bulletin için --competition, --date-from ve --date-to zorunludur")
            print(run_bulletin_live(args.competition, args.date_from, args.date_to, args.season, args.sport_key))
            return

        if not args.home_team_id or not args.away_team_id:
            parser.error(
                "--demo/--bulletin-demo/--bulletin kullanmıyorsanız "
                "--home-team-id ve --away-team-id zorunludur"
            )

        print(
            run_live(
                args.home_team_id,
                args.away_team_id,
                args.home_name,
                args.away_name,
                args.season,
                args.sport_key,
            )
        )
    except Exception as exc:  # noqa: BLE001 - CLI için kullanıcıya okunabilir hata gösterimi
        print(f"Hata: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
