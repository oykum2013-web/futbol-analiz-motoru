"""Tahmin Ajanı.

Form ve H2H ajanlarının çıktısını birleştirip olasılık tabanlı bir maç sonucu
tahmini üretir. Bilinçli olarak basit ve açıklanabilir bir sezgisel (heuristic)
model kullanır — rastgele sayı üretmez, "kesin sonuç" iddia etmez.
"""

from ..schemas import FormReport, H2HReport, Prediction

HOME_ADVANTAGE = 0.15
MIN_STRENGTH = 0.05
H2H_WEIGHT = 0.3
DRAW_BASE = 0.20
DRAW_CLOSENESS_WEIGHT = 0.15


def _team_strength(form: FormReport) -> float:
    """Maç başı puan ve averaja dayalı basit bir güç skoru üretir."""
    if form.matches_considered == 0:
        return 1.0  # veri yoksa nötr kabul et
    points_per_game = form.points / form.matches_considered  # 0..3
    goal_diff_per_game = (form.goals_for - form.goals_against) / form.matches_considered
    return max(MIN_STRENGTH, points_per_game + goal_diff_per_game * 0.5)


def predict(home_form: FormReport, away_form: FormReport, h2h: H2HReport) -> Prediction:
    home_strength = _team_strength(home_form) + HOME_ADVANTAGE
    away_strength = _team_strength(away_form)

    rationale = [
        f"{home_form.team.name} son {home_form.matches_considered} maç: "
        f"{home_form.wins}G {home_form.draws}B {home_form.losses}M "
        f"(form: {home_form.form_string or '-'})",
        f"{away_form.team.name} son {away_form.matches_considered} maç: "
        f"{away_form.wins}G {away_form.draws}B {away_form.losses}M "
        f"(form: {away_form.form_string or '-'})",
        "Ev sahibi avantajı hesaba katıldı.",
    ]

    if h2h.matches_considered > 0:
        h2h_home_rate = (h2h.home_wins - h2h.away_wins) / h2h.matches_considered
        home_strength += h2h_home_rate * H2H_WEIGHT
        away_strength -= h2h_home_rate * H2H_WEIGHT
        rationale.append(
            f"H2H (son {h2h.matches_considered} karşılaşma): "
            f"{h2h.home_wins}-{h2h.draws}-{h2h.away_wins} (ev-berabere-deplasman)"
        )
    else:
        rationale.append("H2H verisi bulunamadı, bu faktör tahmine dahil edilmedi.")

    home_strength = max(home_strength, MIN_STRENGTH)
    away_strength = max(away_strength, MIN_STRENGTH)

    total = home_strength + away_strength
    home_win_raw = home_strength / total
    away_win_raw = away_strength / total

    closeness = 1 - abs(home_win_raw - away_win_raw)  # 1 = eşit güç, 0 = tek taraflı
    draw_prob = DRAW_BASE + closeness * DRAW_CLOSENESS_WEIGHT

    remaining = 1 - draw_prob
    home_win_prob = remaining * home_win_raw
    away_win_prob = remaining * away_win_raw

    total_check = home_win_prob + draw_prob + away_win_prob
    home_win_prob, draw_prob, away_win_prob = (
        round(home_win_prob / total_check * 100, 1),
        round(draw_prob / total_check * 100, 1),
        round(away_win_prob / total_check * 100, 1),
    )

    sample_size = home_form.matches_considered + away_form.matches_considered + h2h.matches_considered
    if sample_size >= 15:
        confidence = "Orta"
    elif sample_size >= 5:
        confidence = "Düşük"
    else:
        confidence = "Çok Düşük"
    if max(home_win_prob, draw_prob, away_win_prob) >= 55 and sample_size >= 10:
        confidence = "Orta-Yüksek"

    return Prediction(
        home=home_form.team,
        away=away_form.team,
        home_win_prob=home_win_prob,
        draw_prob=draw_prob,
        away_win_prob=away_win_prob,
        confidence=confidence,
        rationale=rationale,
    )
