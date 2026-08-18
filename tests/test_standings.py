from ajan_ordusu.agents.standings_analysis import analyze_standings, normalize_football_data_standings
from ajan_ordusu.schemas import TeamRef

A = TeamRef(id="524", name="Takım A")
B = TeamRef(id="61", name="Takım B")

RAW_TABLE = [
    {
        "position": 1,
        "team": {"id": 524, "name": "Takım A"},
        "playedGames": 10,
        "won": 8,
        "draw": 1,
        "lost": 1,
        "points": 25,
        "goalsFor": 20,
        "goalsAgainst": 5,
    },
    {
        "position": 7,
        "team": {"id": 61, "name": "Takım B"},
        "playedGames": 10,
        "won": 3,
        "draw": 3,
        "lost": 4,
        "points": 12,
        "goalsFor": 10,
        "goalsAgainst": 13,
    },
]


def test_normalize_football_data_standings_keys_by_team_id():
    entries = normalize_football_data_standings(RAW_TABLE)

    assert set(entries.keys()) == {"524", "61"}
    assert entries["524"].points == 25
    assert entries["524"].position == 1
    assert entries["61"].points == 12


def test_analyze_standings_returns_data_available_when_both_teams_found():
    entries = normalize_football_data_standings(RAW_TABLE)

    report = analyze_standings(A, B, entries)

    assert report.data_available is True
    assert report.home_entry.points == 25
    assert report.away_entry.points == 12
    assert report.notes


def test_analyze_standings_reports_no_data_when_table_missing():
    report = analyze_standings(A, B, None)

    assert report.data_available is False
    assert "VERİ YOK" in report.notes[0]


def test_analyze_standings_reports_no_data_when_team_not_in_table():
    entries = normalize_football_data_standings(RAW_TABLE)
    unknown_team = TeamRef(id="999", name="Bilinmeyen Takım")

    report = analyze_standings(A, unknown_team, entries)

    assert report.data_available is False
    assert "Bilinmeyen Takım" in report.notes[0]
