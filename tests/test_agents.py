from ajan_ordusu.agents.form_analysis import analyze_form
from ajan_ordusu.agents.h2h_analysis import analyze_h2h
from ajan_ordusu.agents.orchestrator import run_pipeline
from ajan_ordusu.agents.prediction import predict
from ajan_ordusu.schemas import MatchResult, TeamRef

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
