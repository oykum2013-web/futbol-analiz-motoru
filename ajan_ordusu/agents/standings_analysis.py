"""Puan Durumu Ajanı.

İki takımın güncel lig tablosundaki konumunu (sıra, oynanan maç, puan,
averaj) karşılaştırır. "Form Analiz Ajanı" son N maça bakarken, bu ajan
tüm sezonun (lig performansının) toplam görüntüsünü verir — ikisi farklı
sinyallerdir ve Tahmin Ajanı'nda ayrı ayrı değerlendirilir.

Veri bütünlüğü kuralı: bir takım lig tablosunda bulunamazsa (ör. farklı
bir kupada oynuyor, tabloya henüz düşmemiş yeni sezon), data_available
False olarak işaretlenir ve açıkça "veri yok" raporlanır.
"""

from typing import Dict, List, Optional

from ..schemas import StandingsEntry, StandingsReport, TeamRef


def normalize_football_data_standings(raw_table: List[dict]) -> Dict[str, StandingsEntry]:
    """football-data.org /competitions/{code}/standings çıktısını takım id -> StandingsEntry eşler."""
    entries: Dict[str, StandingsEntry] = {}
    for row in raw_table:
        team = row.get("team") or {}
        team_id = team.get("id")
        if team_id is None:
            continue
        entries[str(team_id)] = StandingsEntry(
            team=TeamRef(id=str(team_id), name=team.get("name") or "?"),
            position=row.get("position", 0),
            played=row.get("playedGames", 0),
            won=row.get("won", 0),
            draw=row.get("draw", 0),
            lost=row.get("lost", 0),
            goals_for=row.get("goalsFor", 0),
            goals_against=row.get("goalsAgainst", 0),
            points=row.get("points", 0),
        )
    return entries


def analyze_standings(
    home_team: TeamRef,
    away_team: TeamRef,
    standings_by_team_id: Optional[Dict[str, StandingsEntry]],
) -> StandingsReport:
    if not standings_by_team_id:
        return StandingsReport(
            home=home_team,
            away=away_team,
            data_available=False,
            notes=["Puan durumu verisi bulunamadı — VERİ YOK."],
        )

    home_entry = standings_by_team_id.get(home_team.id)
    away_entry = standings_by_team_id.get(away_team.id)

    if home_entry is None or away_entry is None:
        missing = [t.name for t, e in ((home_team, home_entry), (away_team, away_entry)) if e is None]
        return StandingsReport(
            home=home_team,
            away=away_team,
            data_available=False,
            home_entry=home_entry,
            away_entry=away_entry,
            notes=[f"Lig tablosunda bulunamadı: {', '.join(missing)} — VERİ YOK."],
        )

    return StandingsReport(
        home=home_team,
        away=away_team,
        data_available=True,
        home_entry=home_entry,
        away_entry=away_entry,
        notes=[
            f"{home_team.name}: {home_entry.position}. sıra, {home_entry.points} puan "
            f"({home_entry.played} maç) | {away_team.name}: {away_entry.position}. sıra, "
            f"{away_entry.points} puan ({away_entry.played} maç)"
        ],
    )
