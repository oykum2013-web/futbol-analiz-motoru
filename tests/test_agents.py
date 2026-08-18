from ajan_ordusu.agents.bulletin import format_bulletin_markdown, format_bulletin_message
from ajan_ordusu.agents.form_analysis import analyze_form
from ajan_ordusu.agents.h2h_analysis import analyze_h2h
from ajan_ordusu.agents.market_analysis import analyze_market
from ajan_ordusu.agents.orchestrator import run_pipeline
from ajan_ordusu.agents.prediction import predict
from ajan_ordusu.agents.squad_analysis import analyze_squad
from ajan_ordusu.schemas import InjuryEntry, MatchResult, OddsQuote, PlayerRef, TeamRef

A = TeamRef(id="a", name="Takım A")
B = TeamRef(id="b", name="Takım B")


def test_analyze_form_counts_results_correctly():
    matches = [
        MatchResult("2026-03-01", A, B, 2, 1),  # A galip (ev)
        MatchResult("2026-02-01", B, A, 1, 1),  # A berabere (deplasman)
        MatchResult("2026-01-01", A, B, 0, 2),  # A mağlup (ev)
    ]
    form = analyze_form(A, matches, n=3)

    assert form.matches_considered == 3
    assert form.wins == 1
    assert form.draws == 1
    assert form.losses == 1
    assert form.points == 4
    assert form.form_string == "MBG"  # eskiden yeniye
    assert form.goals_for == 0 + 1 + 2
    assert form.goals_against == 2 + 1 + 1


def test_analyze_form_handles_no_matches():
    form = analyze_form(A, [], n=5)
    assert form.matches_considered == 0
    assert form.avg_goals_for == 0.0
    assert form.form_string == ""


def test_analyze_h2h_normalizes_perspective():
    meetings = [
        MatchResult("2026-01-01", A, B, 2, 0),  # A ev sahibiyken kazandı
        MatchResult("2025-06-01", B, A, 2, 0),  # B ev sahibiyken kazandı -> perspektifte away_wins
    ]
    h2h = analyze_h2h(A, B, meetings, n=5)

    assert h2h.matches_considered == 2
    assert h2h.home_wins == 1  # A'nın kazandığı maç sayısı
    assert h2h.away_wins == 1  # B'nin kazandığı maç sayısı
    assert h2h.draws == 0


def test_predict_favors_team_with_better_form_and_home_advantage():
    strong_form = analyze_form(
        A,
        [
            MatchResult("2026-03-01", A, B, 3, 0),
            MatchResult("2026-02-01", A, B, 2, 0),
            MatchResult("2026-01-01", A, B, 2, 1),
        ],
        n=3,
    )
    weak_form = analyze_form(
        B,
        [
            MatchResult("2026-03-01", B, A, 0, 3),
            MatchResult("2026-02-01", B, A, 0, 2),
            MatchResult("2026-01-01", B, A, 1, 2),
        ],
        n=3,
    )
    empty_h2h = analyze_h2h(A, B, [], n=5)

    prediction = predict(strong_form, weak_form, empty_h2h)

    assert prediction.home_win_prob > prediction.away_win_prob
    total = round(prediction.home_win_prob + prediction.draw_prob + prediction.away_win_prob, 1)
    assert total == 100.0
    assert "kesin" in prediction.disclaimer.lower() or "garanti" in prediction.disclaimer.lower()


def test_run_pipeline_end_to_end_with_demo_style_data():
    home_matches = [MatchResult("2026-01-01", A, B, 1, 0)]
    away_matches = [MatchResult("2026-01-01", A, B, 1, 0)]
    h2h_matches = [MatchResult("2026-01-01", A, B, 1, 0)]

    report = run_pipeline(A, B, home_matches, away_matches, h2h_matches)

    assert report.prediction.home.name == "Takım A"
    assert report.prediction.away.name == "Takım B"
    assert report.home_form.matches_considered == 1
    assert report.h2h.matches_considered == 1
    # Hiçbir kadro verisi verilmedi (None) -> "veri yok" olarak işaretlenmeli,
    # "kadro tam" ile karıştırılmamalı.
    assert report.home_squad.impact_level == "Bilinmiyor"


def test_analyze_squad_with_unknown_data_is_marked_unknown_not_clean():
    squad = analyze_squad(A, None)
    assert squad.impact_score == 0.0
    assert squad.impact_level == "Bilinmiyor"
    assert "veri" in squad.notes[0].lower()


def test_analyze_squad_with_confirmed_empty_list_is_marked_clean():
    squad = analyze_squad(A, [])
    assert squad.impact_score == 0.0
    assert squad.impact_level == "Yok"
    assert "sorgulandı" in squad.notes[0].lower()


def test_analyze_squad_weighs_key_players_more():
    normal_only = analyze_squad(
        A, [InjuryEntry(PlayerRef(id="p1", name="Oyuncu 1"), "Sakatlık", importance=1.0)]
    )
    with_key_player = analyze_squad(
        A, [InjuryEntry(PlayerRef(id="p2", name="Yıldız Oyuncu"), "Sakatlık", importance=2.0)]
    )

    assert with_key_player.impact_score > normal_only.impact_score
    assert with_key_player.impact_score <= 1.0


def test_predict_lowers_probability_for_team_with_high_squad_impact():
    even_form_home = analyze_form(A, [MatchResult("2026-01-01", A, B, 1, 1)], n=1)
    even_form_away = analyze_form(B, [MatchResult("2026-01-01", A, B, 1, 1)], n=1)
    empty_h2h = analyze_h2h(A, B, [], n=5)

    baseline = predict(even_form_home, even_form_away, empty_h2h)

    depleted_home_squad = analyze_squad(
        A,
        [
            InjuryEntry(PlayerRef(id="p1", name="Oyuncu 1"), "Sakatlık", importance=2.0),
            InjuryEntry(PlayerRef(id="p2", name="Oyuncu 2"), "Cezalı", importance=2.0),
            InjuryEntry(PlayerRef(id="p3", name="Oyuncu 3"), "Sakatlık", importance=2.0),
        ],
    )
    with_injuries = predict(even_form_home, even_form_away, empty_h2h, home_squad=depleted_home_squad)

    assert with_injuries.home_win_prob < baseline.home_win_prob
    assert any("kadro etkisi" in r.lower() for r in with_injuries.rationale)


def test_predict_flags_missing_form_data_instead_of_faking_it():
    no_data_form = analyze_form(A, [], n=5)  # takım için hiç maç verisi yok
    real_form = analyze_form(B, [MatchResult("2026-01-01", B, A, 2, 0)], n=1)
    empty_h2h = analyze_h2h(A, B, [], n=5)

    prediction = predict(no_data_form, real_form, empty_h2h)

    assert prediction.confidence == "Yetersiz Veri"
    assert any("VERİ YOK" in r for r in prediction.rationale)
    assert any("UYARI" in r for r in prediction.rationale)


def test_analyze_market_with_no_quotes_reports_no_data():
    market = analyze_market(A, B, None)
    assert market.data_available is False
    assert market.consensus_home_prob is None
    assert any("VERİ YOK" in n for n in market.notes)


def test_analyze_market_devigs_and_averages_real_odds():
    quotes = [
        OddsQuote(bookmaker="Kitapçı 1", home_odds=2.00, draw_odds=3.00, away_odds=4.00),
        OddsQuote(bookmaker="Kitapçı 2", home_odds=2.10, draw_odds=3.10, away_odds=3.90),
    ]
    market = analyze_market(A, B, quotes)

    assert market.data_available is True
    total = round(market.consensus_home_prob + market.consensus_draw_prob + market.consensus_away_prob, 1)
    assert total == 100.0
    # Ev sahibi en düşük orana (en yüksek olasılığa) sahip -> en yüksek zımni olasılık ev sahibinde olmalı
    assert market.consensus_home_prob > market.consensus_draw_prob > market.consensus_away_prob


def test_predict_blends_model_with_real_market_consensus():
    form_home = analyze_form(A, [MatchResult("2026-01-01", A, B, 1, 1)], n=1)
    form_away = analyze_form(B, [MatchResult("2026-01-01", A, B, 1, 1)], n=1)
    empty_h2h = analyze_h2h(A, B, [], n=5)

    baseline = predict(form_home, form_away, empty_h2h)

    lopsided_market = analyze_market(
        A,
        B,
        [OddsQuote(bookmaker="Kitapçı", home_odds=1.20, draw_odds=6.00, away_odds=12.00)],
    )
    with_market = predict(form_home, form_away, empty_h2h, market=lopsided_market)

    assert with_market.home_win_prob > baseline.home_win_prob
    total = round(with_market.home_win_prob + with_market.draw_prob + with_market.away_win_prob, 1)
    assert total == 100.0
    assert any("piyasa" in r.lower() for r in with_market.rationale)


def test_predict_notes_missing_market_data_without_faking_it():
    form_home = analyze_form(A, [MatchResult("2026-01-01", A, B, 1, 1)], n=1)
    form_away = analyze_form(B, [MatchResult("2026-01-01", A, B, 1, 1)], n=1)
    empty_h2h = analyze_h2h(A, B, [], n=5)
    no_market = analyze_market(A, B, None)

    prediction = predict(form_home, form_away, empty_h2h, market=no_market)

    assert any("VERİ YOK" in n or "bulunamadı" in n.lower() for n in [prediction.rationale[-1]])


C = TeamRef(id="c", name="Takım C")
D = TeamRef(id="d", name="Takım D")


def test_bulletin_flags_low_confidence_and_data_gaps():
    well_supported = run_pipeline(
        A,
        B,
        [MatchResult("2026-01-01", A, B, 2, 0)],
        [MatchResult("2026-01-01", A, B, 2, 0)],
        [MatchResult("2026-01-01", A, B, 2, 0)],
        [],  # sakatlık kaynağı sorgulandı, eksik yok
        [],
        [OddsQuote(bookmaker="Kitapçı", home_odds=1.80, draw_odds=3.60, away_odds=4.20)],
    )
    no_data_match = run_pipeline(C, D, [], [], [])  # hiç veri yok -> tüm ajanlar "veri yok" demeli

    bulletin = format_bulletin_markdown([well_supported, no_data_match], title="Test Bülteni")

    assert "Test Bülteni" in bulletin
    assert "RİSK UYARISI" in bulletin
    # İyi desteklenen maç için "eksik veri yok" görülmeli.
    assert "yok (tüm kaynaklar sorgulandı)" in bulletin
    # Veri eksikliği olan maç için uyarı ve gerekçe görülmeli.
    assert "Yetersiz Veri" in bulletin
    assert "form verisi yok" in bulletin
    assert "kadro/sakatlık verisi yok" in bulletin
    assert "Oran/piyasa verisi yok" in bulletin


def test_bulletin_markdown_handles_empty_match_list():
    bulletin = format_bulletin_markdown([], title="Boş Bülten")
    assert "Boş Bülten" in bulletin
    assert "bulunamadı" in bulletin.lower()
    assert "RİSK UYARISI" in bulletin


def test_bulletin_message_format_is_compact_and_still_warns():
    no_data_match = run_pipeline(C, D, [], [], [])
    message = format_bulletin_message([no_data_match], title="Kısa Bülten")

    assert "Kısa Bülten" in message
    assert "RİSK UYARISI" in message
    assert "⚠️" in message
    assert "Eksik veri" in message
