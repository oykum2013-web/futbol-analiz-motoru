"""CLI giriş noktası: tek bir maç için uçtan uca analiz/tahmin üretir.

Kullanım:
    # Ağ/anahtar gerektirmeyen demo mod (örnek/kurgusal veriyle pipeline testi):
    python -m ajan_ordusu.main --demo

    # Gerçek veri ile (football-data.org, FOOTBALL_DATA_API_TOKEN gerektirir):
    python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --match-id 12345

    # Sakatlık/kadro verisi de dahil etmek için (API-Football, API_FOOTBALL_KEY gerektirir):
    python -m ajan_ordusu.main --home-team-id 524 --away-team-id 61 --season 2025
"""

import argparse
import sys

from .agents.data_collection import (
    filter_h2h_matches,
    filter_team_matches,
    normalize_football_data_matches,
)
from .agents.orchestrator import format_report_markdown, run_pipeline
from .agents.squad_analysis import normalize_api_football_injuries
from .clients.api_football import ApiFootballClient, ApiFootballClientError
from .clients.football_data import FootballDataClient
from .schemas import TeamRef


def run_demo() -> str:
    from .sample_data.demo_match import (
        H2H_MACLAR,
        TAKIM_A,
        TAKIM_A_EKSIKLER,
        TAKIM_A_SON_MACLAR,
        TAKIM_B,
        TAKIM_B_EKSIKLER,
        TAKIM_B_SON_MACLAR,
    )

    report = run_pipeline(
        TAKIM_A,
        TAKIM_B,
        TAKIM_A_SON_MACLAR,
        TAKIM_B_SON_MACLAR,
        H2H_MACLAR,
        TAKIM_A_EKSIKLER,
        TAKIM_B_EKSIKLER,
    )
    return format_report_markdown(report)


def _fetch_missing_players(team_id: str, season: int):
    """API_FOOTBALL_KEY tanımlıysa sakatlık/kadro verisini çeker; yoksa sessizce atlar."""
    try:
        client = ApiFootballClient()
    except ApiFootballClientError:
        return None
    raw = client.get_team_injuries(int(team_id), season)
    return normalize_api_football_injuries(raw)


def run_live(home_team_id: str, away_team_id: str, home_name: str, away_name: str, season: int) -> str:
    client = FootballDataClient()
    home_team = TeamRef(id=home_team_id, name=home_name)
    away_team = TeamRef(id=away_team_id, name=away_name)

    home_raw = client.get_team_matches(int(home_team_id), status="FINISHED", limit=10)
    away_raw = client.get_team_matches(int(away_team_id), status="FINISHED", limit=10)

    home_matches = filter_team_matches(normalize_football_data_matches(home_raw), home_team_id)
    away_matches = filter_team_matches(normalize_football_data_matches(away_raw), away_team_id)
    # H2H: iki takımın maç listelerinin birleşiminden ortak karşılaşmaları çıkar.
    h2h_matches = filter_h2h_matches(home_matches + away_matches, home_team_id, away_team_id)

    home_missing = _fetch_missing_players(home_team_id, season)
    away_missing = _fetch_missing_players(away_team_id, season)

    report = run_pipeline(
        home_team, away_team, home_matches, away_matches, h2h_matches, home_missing, away_missing
    )
    return format_report_markdown(report)


def main() -> None:
    parser = argparse.ArgumentParser(description="Tek maç için ajan ordusu analiz/tahmin pipeline'ı")
    parser.add_argument("--demo", action="store_true", help="Ağ/anahtar gerektirmeyen örnek veriyle çalıştır")
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
    args = parser.parse_args()

    if args.demo:
        print(run_demo())
        return

    if not args.home_team_id or not args.away_team_id:
        parser.error("--demo kullanmıyorsanız --home-team-id ve --away-team-id zorunludur")

    try:
        print(run_live(args.home_team_id, args.away_team_id, args.home_name, args.away_name, args.season))
    except Exception as exc:  # noqa: BLE001 - CLI için kullanıcıya okunabilir hata gösterimi
        print(f"Hata: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
