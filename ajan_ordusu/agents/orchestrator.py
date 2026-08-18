"""Orkestratör / Baş Ajan.

Diğer ajanları (form, H2H, kadro, oran/piyasa, tahmin) sırayla tetikler ve
tek bir maç için uçtan uca bir analiz raporu üretir.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from .. import config
from ..schemas import (
    FormReport,
    H2HReport,
    InjuryEntry,
    MarketReport,
    MatchResult,
    OddsQuote,
    Prediction,
    StandingsEntry,
    StandingsReport,
    SquadReport,
    TeamRef,
)
from .form_analysis import analyze_form
from .h2h_analysis import analyze_h2h
from .market_analysis import analyze_market
from .prediction import predict
from .squad_analysis import analyze_squad
from .standings_analysis import analyze_standings
from .validation import ValidationResult, format_validation_markdown, validate_and_fix


@dataclass
class MatchAnalysisReport:
    home_form: FormReport
    away_form: FormReport
    h2h: H2HReport
    home_squad: SquadReport
    away_squad: SquadReport
    market: MarketReport
    standings: StandingsReport
    prediction: Prediction
    validation: ValidationResult


def run_pipeline(
    home_team: TeamRef,
    away_team: TeamRef,
    home_recent_matches: List[MatchResult],
    away_recent_matches: List[MatchResult],
    h2h_matches: List[MatchResult],
    home_missing_players: Optional[List[InjuryEntry]] = None,
    away_missing_players: Optional[List[InjuryEntry]] = None,
    odds_quotes: Optional[List[OddsQuote]] = None,
    standings_by_team_id: Optional[Dict[str, StandingsEntry]] = None,
    form_n: int = config.DEFAULT_FORM_MATCHES,
    h2h_n: int = config.DEFAULT_H2H_MATCHES,
) -> MatchAnalysisReport:
    home_form = analyze_form(home_team, home_recent_matches, n=form_n)
    away_form = analyze_form(away_team, away_recent_matches, n=form_n)
    h2h = analyze_h2h(home_team, away_team, h2h_matches, n=h2h_n)
    home_squad = analyze_squad(home_team, home_missing_players)
    away_squad = analyze_squad(away_team, away_missing_players)
    market = analyze_market(home_team, away_team, odds_quotes)
    standings = analyze_standings(home_team, away_team, standings_by_team_id)
    prediction = predict(home_form, away_form, h2h, home_squad, away_squad, market, standings)
    validation = validate_and_fix(home_form, away_form, prediction)
    return MatchAnalysisReport(
        home_form=home_form,
        away_form=away_form,
        h2h=h2h,
        home_squad=home_squad,
        away_squad=away_squad,
        market=market,
        standings=standings,
        prediction=prediction,
        validation=validation,
    )


_NO_SOURCE = (
    "VERİ YETERSİZ — bu proje için entegre edilmiş gerçek bir kaynak yok "
    "(bkz. veri bütünlüğü kuralı: tahmini/uydurma veri üretilmez)."
)


def _h2h_edge_note(h2h: H2HReport) -> str:
    if h2h.matches_considered == 0:
        return "Psikolojik üstünlük: H2H verisi yok — değerlendirilemedi."
    if h2h.home_wins > h2h.away_wins:
        return f"Psikolojik üstünlük: son karşılaşmalara göre {h2h.home.name} lehine hafif eğilim."
    if h2h.away_wins > h2h.home_wins:
        return f"Psikolojik üstünlük: son karşılaşmalara göre {h2h.away.name} lehine hafif eğilim."
    return "Psikolojik üstünlük: son karşılaşmalar dengeli, belirgin bir üstünlük yok."


def _goal_expectation_note(p: Prediction, home_form: FormReport, away_form: FormReport) -> str:
    if home_form.matches_considered == 0 or away_form.matches_considered == 0:
        return "Olası skor aralığı: VERİ YETERSİZ (form verisi eksik olduğundan hesaplanamadı)."
    exp_home = round((home_form.avg_goals_for + away_form.avg_goals_against) / 2, 1)
    exp_away = round((away_form.avg_goals_for + home_form.avg_goals_against) / 2, 1)
    return (
        f"Olası skor aralığı (kaba gösterge): {p.home.name} ~{exp_home}, {p.away.name} ~{exp_away} gol — "
        "son maçlardaki gerçek gol averajlarının ortalamasına dayanır, bir xG modeli DEĞİLDİR."
    )


def format_report_markdown(report: MatchAnalysisReport) -> str:
    p = report.prediction
    m = report.market
    hf, af = report.home_form, report.away_form

    if m.data_available:
        market_lines = [
            f"- Piyasa konsensüsü: Ev %{m.consensus_home_prob}, Beraberlik %{m.consensus_draw_prob}, "
            f"Deplasman %{m.consensus_away_prob}"
            + (f" — {m.notes[0]}" if m.notes else "")
        ]
    else:
        market_lines = [f"- {m.notes[0] if m.notes else 'Oran verisi bulunamadı — VERİ YOK.'}"]

    standings_lines = (
        [f"- {n}" for n in report.standings.notes]
        if report.standings.notes
        else ["- Puan durumu verisi bulunamadı — VERİ YOK."]
    )

    lines = [
        f"# {p.home.name} vs {p.away.name} — Ön Maç Analizi",
        "",
        "## 1. Form Durumu",
        f"- **{hf.team.name}**: {hf.wins}G {hf.draws}B {hf.losses}M, "
        f"ort. gol {hf.avg_goals_for}-{hf.avg_goals_against} (form: {hf.form_string or '-'})",
        f"- **{af.team.name}**: {af.wins}G {af.draws}B {af.losses}M, "
        f"ort. gol {af.avg_goals_for}-{af.avg_goals_against} (form: {af.form_string or '-'})",
        f"- İç saha/deplasman ayrıştırılmış performans: {_NO_SOURCE} "
        "(Form Ajanı şu an sadece venue'dan bağımsız son N maça bakıyor.)",
        "",
        "## 2. Kadro ve Eksikler",
        f"- **{report.home_squad.team.name}**: {report.home_squad.impact_level} etki "
        f"({len(report.home_squad.missing_players)} eksik oyuncu)"
        + (f" — {report.home_squad.notes[0]}" if report.home_squad.notes else ""),
        f"- **{report.away_squad.team.name}**: {report.away_squad.impact_level} etki "
        f"({len(report.away_squad.missing_players)} eksik oyuncu)"
        + (f" — {report.away_squad.notes[0]}" if report.away_squad.notes else ""),
        f"- Olası 11 / rotasyon ihtimali: {_NO_SOURCE}",
        "",
        "## 3. Karşılıklı Geçmiş (H2H)",
        f"- Son {report.h2h.matches_considered} karşılaşma: "
        f"{report.h2h.home_wins} {report.h2h.home.name} galibiyeti, "
        f"{report.h2h.draws} beraberlik, "
        f"{report.h2h.away_wins} {report.h2h.away.name} galibiyeti",
        f"- {_h2h_edge_note(report.h2h)}",
        "",
        "## 4. Taktiksel Kıyaslama",
        f"- Oyun sistemi/stil, güçlü-zayıf yön eşleşmesi, duran top etkinliği: {_NO_SOURCE}",
        "",
        "## 5. İstatistiksel Veriler",
        f"- xG, topla oynama, isabetli şut, korner, kart/faul eğilimi: {_NO_SOURCE}",
        "- Bilinen tek gerçek istatistik gol averajlarıdır (bkz. Form Durumu) — ayrıca aşağıya bakınız.",
        "",
        "## 6. Bağlamsal Faktörler",
        *standings_lines,
        *market_lines,
        f"- Motivasyon farkı: {_NO_SOURCE}",
        f"- Hava durumu / saha koşulları: {_NO_SOURCE}",
        f"- Hakem istatistikleri: {_NO_SOURCE}",
        "",
        "## 7. Sonuç ve Tahmin",
        f"- {p.home.name} kazanır: **%{p.home_win_prob}**",
        f"- Beraberlik: **%{p.draw_prob}**",
        f"- {p.away.name} kazanır: **%{p.away_win_prob}**",
        f"- Güven düzeyi: {p.confidence}",
        f"- {_goal_expectation_note(p, hf, af)}",
        "",
        "### Gerekçe",
        *[f"- {r}" for r in p.rationale],
        "",
        f"> ⚠️ {p.disclaimer}",
        "",
        format_validation_markdown(report.validation),
    ]
    return "\n".join(lines)
