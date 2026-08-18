from ajan_ordusu.agents.validation import validate_and_fix
from ajan_ordusu.schemas import FormReport, Prediction, TeamRef

A = TeamRef(id="a", name="Takım A")
B = TeamRef(id="b", name="Takım B")


def _form(matches_considered: int) -> FormReport:
    return FormReport(
        team=A,
        matches_considered=matches_considered,
        wins=0,
        draws=0,
        losses=0,
        goals_for=0,
        goals_against=0,
        points=0,
        form_string="",
        avg_goals_for=0.0,
        avg_goals_against=0.0,
    )


def test_validate_and_fix_corrects_small_rounding_drift():
    prediction = Prediction(
        home=A, away=B, home_win_prob=40.1, draw_prob=30.2, away_win_prob=29.4, confidence="Orta"
    )  # toplam 99.7, 100'e olan fark 0.3 -> otomatik düzeltilmeli

    result = validate_and_fix(_form(10), _form(10), prediction)

    assert round(prediction.home_win_prob + prediction.draw_prob + prediction.away_win_prob, 1) == 100.0
    assert any("Olasılık toplamı" in msg for msg in result.fixed)
    assert result.ok


def test_validate_and_fix_flags_large_probability_drift_as_unresolved():
    prediction = Prediction(
        home=A, away=B, home_win_prob=40.0, draw_prob=30.0, away_win_prob=10.0, confidence="Orta"
    )  # toplam 80 -> otomatik düzeltme için çok büyük bir fark, gerçek bir hata olmalı

    result = validate_and_fix(_form(10), _form(10), prediction)

    assert not result.ok
    assert any("Olasılık toplamı" in msg for msg in result.unresolved)
    # Otomatik düzeltme reddedildiği için değerler değiştirilmemiş olmalı.
    assert prediction.home_win_prob == 40.0


def test_validate_and_fix_flags_out_of_range_probability():
    prediction = Prediction(
        home=A, away=B, home_win_prob=140.0, draw_prob=-20.0, away_win_prob=-20.0, confidence="Orta"
    )

    result = validate_and_fix(_form(10), _form(10), prediction)

    assert not result.ok
    assert any("aralık dışı" in msg for msg in result.unresolved)


def test_validate_and_fix_forces_confidence_when_form_data_missing():
    prediction = Prediction(
        home=A, away=B, home_win_prob=40.0, draw_prob=30.0, away_win_prob=30.0, confidence="Orta-Yüksek"
    )

    result = validate_and_fix(_form(0), _form(10), prediction)

    assert prediction.confidence == "Yetersiz Veri"
    assert any("Yetersiz Veri" in msg for msg in result.fixed)


def test_validate_and_fix_reports_clean_when_nothing_wrong():
    prediction = Prediction(
        home=A, away=B, home_win_prob=40.0, draw_prob=30.0, away_win_prob=30.0, confidence="Orta"
    )

    result = validate_and_fix(_form(10), _form(10), prediction)

    assert result.ok
    assert result.fixed == []
    assert result.unresolved == []
