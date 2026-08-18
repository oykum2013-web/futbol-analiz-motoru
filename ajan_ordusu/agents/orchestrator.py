"""Orkestratör / Baş Ajan.

Diğer ajanları (form, H2H, tahmin) sırayla tetikler ve tek bir maç için
uçtan uca bir analiz raporu üretir.
"""

from dataclasses import dataclass
from typing import List

from .. import config
from ..schemas import FormReport, H2HReport, MatchResult, Prediction, TeamRef
from .form_analysis import analyze_form
from .h2h_analysis import analyze_h2h
from .prediction import predict


@dataclass
class MatchAnalysisReport:
    home_form: FormReport
    away_form: FormReport
    h2h: H2HReport
    prediction: Prediction


def run_pipeline(
    home_team: TeamRef,
    away_team: TeamRef,
    home_recent_matches: List[MatchResult],
    away_recent_matches: List[MatchResult],
    h2h_matches: List[MatchResult],
    form_n: int = config.DEFAULT_FORM_MATCHES,
    h2h_n: int = config.DEFAULT_H2H_MATCHES,
) -> MatchAnalysisReport:
    home_form = analyze_form(home_team, home_recent_matches, n=form_n)
    away_form = analyze_form(away_team, away_recent_matches, n=form_n)
    h2h = analyze_h2h(home_team, away_team, h2h_matches, n=h2h_n)
    prediction = predict(home_form, away_form, h2h)
    return MatchAnalysisReport(home_form=home_form, away_form=away_form, h2h=h2h, prediction=prediction)


def format_report_markdown(report: MatchAnalysisReport) -> str:
    p = report.prediction
    lines = [
        f"# {p.home.name} vs {p.away.name} — Analiz Raporu",
        "",
        "## Form",
        f"- **{report.home_form.team.name}**: {report.home_form.wins}G "
        f"{report.home_form.draws}B {report.home_form.losses}M, "
        f"ort. gol {report.home_form.avg_goals_for}-{report.home_form.avg_goals_against} "
        f"(form: {report.home_form.form_string or '-'})",
        f"- **{report.away_form.team.name}**: {report.away_form.wins}G "
        f"{report.away_form.draws}B {report.away_form.losses}M, "
        f"ort. gol {report.away_form.avg_goals_for}-{report.away_form.avg_goals_against} "
        f"(form: {report.away_form.form_string or '-'})",
        "",
        "## Head-to-Head",
        f"- Son {report.h2h.matches_considered} karşılaşma: "
        f"{report.h2h.home_wins} {report.h2h.home.name} galibiyeti, "
        f"{report.h2h.draws} beraberlik, "
        f"{report.h2h.away_wins} {report.h2h.away.name} galibiyeti",
        "",
        "## Tahmin",
        f"- {p.home.name} kazanır: **%{p.home_win_prob}**",
        f"- Beraberlik: **%{p.draw_prob}**",
        f"- {p.away.name} kazanır: **%{p.away_win_prob}**",
        f"- Güven düzeyi: {p.confidence}",
        "",
        "### Gerekçe",
        *[f"- {r}" for r in p.rationale],
        "",
        f"> ⚠️ {p.disclaimer}",
    ]
    return "\n".join(lines)
