"""Head-to-Head (H2H) Ajanı.

İki takım arasındaki geçmiş karşılaşmaları, sonucu tahmin edilecek maçtaki
ev sahibi/deplasman perspektifine göre normalize ederek özetler.
"""

from typing import List

from .. import config
from ..schemas import H2HReport, MatchResult, TeamRef


def analyze_h2h(
    home: TeamRef, away: TeamRef, meetings: List[MatchResult], n: int = config.DEFAULT_H2H_MATCHES
) -> H2HReport:
    """`meetings`in en yeniden en eskiye sıralı, bitmiş karşılaşmalar olduğu varsayılır."""
    considered = meetings[:n]

    home_wins = away_wins = draws = home_goals = away_goals = 0

    for match in considered:
        if match.home.id == home.id:
            hg, ag = match.home_goals, match.away_goals
        else:
            hg, ag = match.away_goals, match.home_goals
        if hg is None or ag is None:
            continue

        home_goals += hg
        away_goals += ag
        if hg > ag:
            home_wins += 1
        elif hg < ag:
            away_wins += 1
        else:
            draws += 1

    return H2HReport(
        home=home,
        away=away,
        matches_considered=len(considered),
        home_wins=home_wins,
        away_wins=away_wins,
        draws=draws,
        home_goals=home_goals,
        away_goals=away_goals,
        last_meetings=considered,
    )
