"""mackolik.com'un Süper Lig puan durumu sayfasından GERÇEKTEN çekilmiş ham
`fetch_tables()` çıktısıyla (bkz. proje geçmişi — local ortamda canlı test
edildi) doğrulanır; uydurma/örnek veri değildir."""

from ajan_ordusu.agents.mackolik_standings import (
    format_mackolik_standings_markdown,
    parse_mackolik_standings_rows,
)

REAL_MACKOLIK_ROWS = [
    ["#", "", "TAKIM", "O", "+/-", "G", "B", "M", "A", "Y", "AV", "P"],
    ["1", "", "Amed SK", "1", "3", "1", "0", "0", "3", "0", "3", "3"],
    ["2", "", "Başakşehir", "1", "2", "1", "0", "0", "2", "0", "2", "3"],
    ["3", "", "Gençlerbirliği", "1", "1", "1", "0", "0", "2", "1", "1", "3"],
]


def test_parse_skips_header_row():
    entries = parse_mackolik_standings_rows(REAL_MACKOLIK_ROWS)
    assert len(entries) == 3  # başlık satırı hariç


def test_parse_maps_columns_correctly():
    entries = parse_mackolik_standings_rows(REAL_MACKOLIK_ROWS)
    amed = entries[0]
    assert amed.team.name == "Amed SK"
    assert amed.position == 1
    assert amed.played == 1
    assert amed.won == 1
    assert amed.draw == 0
    assert amed.lost == 0
    assert amed.goals_for == 3
    assert amed.goals_against == 0
    assert amed.points == 3


def test_parse_ignores_short_or_malformed_rows():
    rows = REAL_MACKOLIK_ROWS + [["yalnızca", "bir", "kaç", "hücre"]]
    entries = parse_mackolik_standings_rows(rows)
    assert len(entries) == 3  # bozuk satır sessizce atlanır, uydurulmaz


def test_parse_returns_empty_list_for_unrelated_table():
    unrelated = [["Ad", "Soyad"], ["Ali", "Veli"]]
    assert parse_mackolik_standings_rows(unrelated) == []


def test_format_markdown_includes_all_teams_and_goal_diff():
    entries = parse_mackolik_standings_rows(REAL_MACKOLIK_ROWS)
    md = format_mackolik_standings_markdown(entries, title="Süper Lig Puan Durumu")
    assert "Süper Lig Puan Durumu" in md
    assert "Amed SK" in md
    assert "+3" in md  # Amed SK averajı: 3-0
    assert "Gençlerbirliği" in md
