"""Form Analiz Ajanı.

Bir takımın son N maçtaki galibiyet/beraberlik/mağlubiyet ve gol istatistiklerini
değerlendirir.
"""

from typing import List

from .. import config
from ..schemas import FormReport, MatchResult, TeamRef


def analyze_form(
    team: TeamRef, recent_matches: List[MatchResult], n: int = config.DEFAULT_FORM_MATCHES
) -> FormReport:
    """`recent_matches`in en yeniden en eskiye sıralı, bitmiş maçlar olduğu varsayılır."""
    considered = recent_matches[:n]

    wins = draws = losses = goals_for = goals_against = 0
    form_chars = []

    # form_string'i eskiden yeniye okunabilir sırada oluşturmak için ters çeviriyoruz.
    for match in reversed(considered):
        is_home = match.home.id == team.id
        team_goals = match.home_goals if is_home else match.away_goals
        opp_goals = match.away_goals if is_home else match.home_goals
        if team_goals is None or opp_goals is None:
            continue

        goals_for += team_goals
        goals_against += opp_goals

        if team_goals > opp_goals:
            wins += 1
            form_chars.append("G")
        elif team_goals == opp_goals:
            draws += 1
            form_chars.append("B")
        else:
            losses += 1
            form_chars.append("M")

    played = wins + draws + losses
    return FormReport(
        team=team,
        matches_considered=played,
        wins=wins,
        draws=draws,
        losses=losses,
        goals_for=goals_for,
        goals_against=goals_against,
        points=wins * 3 + draws,
        form_string="".join(form_chars),
        avg_goals_for=round(goals_for / played, 2) if played else 0.0,
        avg_goals_against=round(goals_against / played, 2) if played else 0.0,
    )
