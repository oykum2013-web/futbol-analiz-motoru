"""Veri Toplama Ajanı.

Farklı kaynaklardan (football-data.org, OpenLigaDB, ya da örnek/demo veri)
gelen ham maç verisini ortak `MatchResult` şemasına normalize eder.
"""

from typing import Any, Dict, List, Optional

from ..schemas import MatchResult, TeamRef


def normalize_football_data_matches(raw_matches: List[Dict[str, Any]]) -> List[MatchResult]:
    """football-data.org v4 /teams/{id}/matches veya /competitions/.../matches çıktısını normalize eder."""
    normalized = []
    for m in raw_matches:
        home = m.get("homeTeam", {}) or {}
        away = m.get("awayTeam", {}) or {}
        score = (m.get("score", {}) or {}).get("fullTime", {}) or {}
        normalized.append(
            MatchResult(
                date=(m.get("utcDate") or "")[:10],
                home=TeamRef(id=str(home.get("id")), name=home.get("name") or home.get("shortName") or "?"),
                away=TeamRef(id=str(away.get("id")), name=away.get("name") or away.get("shortName") or "?"),
                home_goals=score.get("home"),
                away_goals=score.get("away"),
                competition=(m.get("competition") or {}).get("name"),
            )
        )
    return normalized


def normalize_openligadb_matches(raw_matches: List[Dict[str, Any]]) -> List[MatchResult]:
    """OpenLigaDB /getmatchdata/... çıktısını normalize eder (yalnızca bitmiş maçlar)."""
    normalized = []
    for m in raw_matches:
        if not m.get("matchIsFinished"):
            continue
        results = m.get("matchResults") or []
        # resultTypeID == 2 "Endergebnis" (maç sonucu); yoksa listedeki son sonucu kullan.
        final = next((r for r in results if r.get("resultTypeID") == 2), None)
        if final is None and results:
            final = results[-1]
        home_goals = final.get("pointsTeam1") if final else None
        away_goals = final.get("pointsTeam2") if final else None
        team1 = m.get("team1", {}) or {}
        team2 = m.get("team2", {}) or {}
        normalized.append(
            MatchResult(
                date=(m.get("matchDateTime") or "")[:10],
                home=TeamRef(id=str(team1.get("teamId")), name=team1.get("teamName") or "?"),
                away=TeamRef(id=str(team2.get("teamId")), name=team2.get("teamName") or "?"),
                home_goals=home_goals,
                away_goals=away_goals,
                competition=m.get("leagueName"),
            )
        )
    return normalized


def filter_team_matches(matches: List[MatchResult], team_id: str) -> List[MatchResult]:
    """Belirli bir takımın yer aldığı, bitmiş maçları en yeniden en eskiye sıralar."""
    team_matches = [m for m in matches if m.is_finished and (m.home.id == team_id or m.away.id == team_id)]
    return sorted(team_matches, key=lambda m: m.date, reverse=True)


def filter_h2h_matches(matches: List[MatchResult], team_a_id: str, team_b_id: str) -> List[MatchResult]:
    """İki takım arasındaki bitmiş karşılaşmaları en yeniden en eskiye sıralar."""
    pairs = {frozenset((team_a_id, team_b_id))}
    h2h = [m for m in matches if m.is_finished and frozenset((m.home.id, m.away.id)) in pairs]
    return sorted(h2h, key=lambda m: m.date, reverse=True)
