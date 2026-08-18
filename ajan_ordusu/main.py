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
from typing import Dict, List, Optional

import requests

from . import config
from .agents.bulletin import format_bulletin_markdown
from .agents.mackolik_standings import (
    MackolikStandingsError,
    fetch_mackolik_standings,
    format_mackolik_standings_markdown,
)
from .agents.web_research import format_web_research_markdown, gather_web_snippets
from .agents.data_collection import (
    filter_h2h_matches,
    filter_team_matches,
    normalize_football_data_matches,
)
from .agents.market_analysis import normalize_the_odds_api_event
from .agents.orchestrator import MatchAnalysisReport, format_report_markdown, run_pipeline
from .agents.squad_analysis import normalize_api_football_injuries
from .agents.standings_analysis import normalize_football_data_standings
from .clients.api_football import ApiFootballClient, ApiFootballClientError
from .clients.football_data import FootballDataClient
from .clients.the_odds_api import TheOddsApiClient, TheOddsApiClientError
from .schemas import StandingsEntry, TeamRef

# --next N kullanıldığında (bkz. --bulletin), gelecek maçları aramak için taranacak
# gün penceresi. Çok dar olursa fikstürü seyrek olan bir lig için N maç bulunamayabilir.
UPCOMING_SEARCH_WINDOW_DAYS = 120

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


def _fetch_standings(client: FootballDataClient, competition_code: Optional[str]) -> Optional[Dict[str, StandingsEntry]]:
    """--competition verilmişse lig tablosunu çeker; yoksa (ya da hata alınırsa) None döner.

    Bültende tüm maçlar için TEK SEFERDE çekilip yeniden kullanılır (bkz.
    build_bulletin_live_reports) — her maç için ayrı ayrı sorgulamak
    football-data.org kotasını gereksiz yere tüketir.
    """
    if not competition_code:
        return None
    try:
        raw_table = client.get_competition_standings(competition_code)
    except requests.exceptions.RequestException as exc:
        logger.warning("'%s' için puan durumu çekilemedi: %s", competition_code, exc)
        return None
    return normalize_football_data_standings(raw_table)


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
    standings_by_team_id: Optional[Dict[str, StandingsEntry]] = None,
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
        standings_by_team_id,
    )


def run_live(
    home_team_id: str,
    away_team_id: str,
    home_name: str,
    away_name: str,
    season: int,
    sport_key: Optional[str] = None,
    competition: Optional[str] = None,
) -> str:
    client = FootballDataClient()
    standings = _fetch_standings(client, competition)
    report = _analyze_live_match(
        client, home_team_id, away_team_id, home_name, away_name, season, sport_key, standings
    )
    return format_report_markdown(report)


def build_bulletin_live_reports(
    competition_code: str,
    date_from: Optional[str],
    date_to: Optional[str],
    season: int,
    sport_key: Optional[str] = None,
    next_n: Optional[int] = None,
) -> list:
    """Bir lig için maç analiz raporlarını üretir.

    `next_n` verilirse `date_from`/`date_to` yok sayılır: bugünden itibaren
    (± `UPCOMING_SEARCH_WINDOW_DAYS` gün) henüz oynanmamış (SCHEDULED/TIMED)
    ilk N fikstür, tarihe göre sıralanıp analiz edilir — "bana N maç analizi
    yap" akışı için tarih aralığını elle hesaplamaya gerek bırakmaz.

    football-data.org'un dakika başı istek limitini korumak için istekler
    arasında otomatik yavaşlatma, istemcinin kendisi tarafından (tüm süreç
    genelinde paylaşılan şekilde) uygulanır — bkz. clients/football_data.py.
    Puan durumu, her maç için ayrı ayrı değil, lig başına TEK SEFERDE çekilir.
    """
    client = FootballDataClient()
    standings = _fetch_standings(client, competition_code)

    if next_n is not None:
        date_from = date.today().isoformat()
        date_to = (date.today() + timedelta(days=UPCOMING_SEARCH_WINDOW_DAYS)).isoformat()

    fixtures = client.get_competition_matches(competition_code, date_from=date_from, date_to=date_to)

    if next_n is not None:
        fixtures = sorted(
            (f for f in fixtures if f.get("status") in ("SCHEDULED", "TIMED")),
            key=lambda f: f.get("utcDate") or "",
        )[:next_n]

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
            standings,
        )
        reports.append(report)
    return reports


def run_bulletin_live(
    competition_code: str,
    date_from: Optional[str],
    date_to: Optional[str],
    season: int,
    sport_key: Optional[str] = None,
    next_n: Optional[int] = None,
) -> str:
    reports = build_bulletin_live_reports(competition_code, date_from, date_to, season, sport_key, next_n)
    if next_n is not None:
        title = f"Sıradaki {next_n} Maç — Tahmin Bülteni ({competition_code})"
    else:
        title = f"{date_from} – {date_to} Tahmin Bülteni ({competition_code})"
    return format_bulletin_markdown(reports, title=title)


def _auto_output_filename(competition_code: str, today: Optional[date] = None) -> str:
    """--bulletin-auto için: kullanıcı --output vermese bile rapor dosyaya kaydedilsin diye
    deterministik bir dosya adı üretir (ör. 'bulten_PL_2026-08-18.md')."""
    today = today or date.today()
    return f"bulten_{competition_code}_{today.isoformat()}.md"


def apply_bulletin_auto_defaults(args: argparse.Namespace, parser: argparse.ArgumentParser) -> None:
    """--bulletin-auto verilmişse, --bulletin'in gerektirdiği argümanlara varsayılan değer
    atar: --competition hâlâ zorunludur (parser.error ile çıkılır), ama tarih aralığı ve
    çıktı dosya adı elle verilmemişse otomatik doldurulur."""
    if not args.bulletin_auto:
        return
    if not args.competition:
        parser.error("--bulletin-auto için --competition zorunludur")
    args.bulletin = True
    if args.next_n is None and not (args.date_from and args.date_to):
        args.next_n = config.DEFAULT_AUTO_BULLETIN_NEXT_N
    if not args.output:
        args.output = _auto_output_filename(args.competition)


def _emit(text: str, output_path: Optional[str]) -> None:
    """Raporu ekrana yazdırır; --output verilmişse aynı zamanda dosyaya kaydeder."""
    print(text)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"\n(Rapor '{output_path}' dosyasına kaydedildi.)", file=sys.stderr)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ajan ordusu analiz/tahmin/bülten pipeline'ı")
    parser.add_argument("--demo", action="store_true", help="Ağ/anahtar gerektirmeyen tek maç örneği")
    parser.add_argument(
        "--bulletin-demo", action="store_true", help="Ağ/anahtar gerektirmeyen çok maçlı bülten örneği"
    )
    parser.add_argument("--bulletin", action="store_true", help="Gerçek veriyle çok maçlı bülten üret")
    parser.add_argument(
        "--bulletin-auto",
        action="store_true",
        help=(
            "--bulletin'in tam otomatik kısayolu: sadece --competition gerekir. Tarih aralığı "
            f"elle verilmezse en yakın {config.DEFAULT_AUTO_BULLETIN_NEXT_N} fikstür otomatik "
            "taranır, --output verilmezse rapor kendiliğinden 'bulten_<LIG>_<tarih>.md' "
            "dosyasına kaydedilir — hiçbir takım ID'si/tarih girmeye gerek yoktur."
        ),
    )
    parser.add_argument(
        "--competition",
        help="--bulletin için football-data.org lig kodu (ör. PL, BL1); tek maç modunda puan durumunu dahil etmek için de kullanılabilir",
    )
    parser.add_argument("--date-from", help="--bulletin için başlangıç tarihi (YYYY-MM-DD)")
    parser.add_argument("--date-to", help="--bulletin için bitiş tarihi (YYYY-MM-DD)")
    parser.add_argument(
        "--next",
        type=int,
        dest="next_n",
        metavar="N",
        help=(
            "--bulletin ile: --date-from/--date-to yerine, bugünden itibaren henüz "
            "oynanmamış ilk N fikstürü otomatik bulup analiz eder (ör. 'sıradaki 20 maçı analiz et')"
        ),
    )
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
    parser.add_argument(
        "--output",
        help="Raporu ekrana yazdırmanın yanında verilen dosya yoluna da (UTF-8, Markdown) kaydeder",
    )
    parser.add_argument(
        "--web-url",
        action="append",
        dest="web_urls",
        metavar="URL",
        help=(
            "Chromium (Playwright) ile ziyaret edilip ham metni rapora ek bölüm olarak eklenecek "
            "URL; birden fazla kez verilebilir. Gerekir: pip install playwright && "
            "playwright install chromium"
        ),
    )
    parser.add_argument(
        "--web-wait-selector",
        help="--web-url sayfaları JS ile geç yükleniyorsa beklenecek CSS seçici (opsiyonel)",
    )
    parser.add_argument(
        "--mackolik-standings-url",
        metavar="URL",
        help=(
            "football-data.org'un ücretsiz planında olmayan ligler (ör. Türkiye Süper Lig) için: "
            "mackolik.com'un puan durumu sayfasını Chromium ile çekip yapılandırılmış bir puan "
            "durumu tablosu (Markdown) üretir. API anahtarı gerektirmez, diğer modlarla birlikte "
            "kullanılmaz — bağımsız bir çalıştırma modudur."
        ),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    def with_web_research(text: str) -> str:
        if not args.web_urls:
            return text
        snippets = gather_web_snippets(args.web_urls, wait_selector=args.web_wait_selector)
        extra = format_web_research_markdown(snippets)
        return f"{text}\n\n{extra}" if extra else text

    if args.mackolik_standings_url:
        try:
            entries = fetch_mackolik_standings(args.mackolik_standings_url)
        except MackolikStandingsError as exc:
            print(f"Hata: {exc}", file=sys.stderr)
            sys.exit(1)
        title = "Puan Durumu (mackolik.com)"
        _emit(format_mackolik_standings_markdown(entries, title=title), args.output)
        return

    if args.demo:
        _emit(with_web_research(run_demo()), args.output)
        return

    if args.bulletin_demo:
        _emit(with_web_research(run_bulletin_demo()), args.output)
        return

    apply_bulletin_auto_defaults(args, parser)

    try:
        if args.bulletin:
            if not args.competition:
                parser.error("--bulletin için --competition zorunludur")
            if args.next_n is None and (not args.date_from or not args.date_to):
                parser.error("--bulletin için --next N ya da (--date-from ve --date-to) verilmelidir")
            if args.next_n is not None and args.next_n <= 0:
                parser.error("--next pozitif bir tam sayı olmalıdır")
            _emit(
                with_web_research(
                    run_bulletin_live(
                        args.competition,
                        args.date_from,
                        args.date_to,
                        args.season,
                        args.sport_key,
                        args.next_n,
                    )
                ),
                args.output,
            )
            return

        if not args.home_team_id or not args.away_team_id:
            parser.error(
                "--demo/--bulletin-demo/--bulletin kullanmıyorsanız "
                "--home-team-id ve --away-team-id zorunludur"
            )

        _emit(
            with_web_research(
                run_live(
                    args.home_team_id,
                    args.away_team_id,
                    args.home_name,
                    args.away_name,
                    args.season,
                    args.sport_key,
                    args.competition,
                )
            ),
            args.output,
        )
    except Exception as exc:  # noqa: BLE001 - CLI için kullanıcıya okunabilir hata gösterimi
        print(f"Hata: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
