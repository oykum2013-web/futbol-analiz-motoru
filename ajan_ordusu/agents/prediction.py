"""Tahmin Ajanı.

Form, H2H ve kadro ajanlarının çıktısını birleştirip olasılık tabanlı bir maç
sonucu tahmini üretir. Bilinçli olarak basit ve açıklanabilir bir sezgisel
(heuristic) model kullanır — rastgele sayı üretmez, "kesin sonuç" iddia etmez.

ÖNEMLİ (veri bütünlüğü kuralı): Bir takım için gerçek form verisi
bulunamadıysa (matches_considered == 0), bu açıkça "veri yok" olarak
raporlanır ve güven düzeyi zorla düşürülür — eksik veri, sonucu etkilemeyen
nötr bir sayıyla sessizce doldurulup gerçek bir istatistikmiş gibi
sunulmaz.
"""

from typing import Optional

from ..schemas import FormReport, H2HReport, Prediction, SquadReport

HOME_ADVANTAGE = 0.15
MIN_STRENGTH = 0.05
H2H_WEIGHT = 0.3
DRAW_BASE = 0.20
DRAW_CLOSENESS_WEIGHT = 0.15
SQUAD_IMPACT_WEIGHT = 0.4


def _team_strength(form: FormReport) -> float:
    """Maç başı puan ve averaja dayalı basit bir güç skoru üretir.

    Veri yoksa (matches_considered == 0) nötr bir değer (1.0) döner; bu bir
    "tahmin" değil, sadece toplamı bozmamak için kullanılan bir yer tutucudur —
    çağıran taraf (predict()) bu durumu ayrıca "veri yok" olarak raporlar ve
    güven düzeyini buna göre düşürür.
    """
    if form.matches_considered == 0:
        return 1.0
    points_per_game = form.points / form.matches_considered  # 0..3
    goal_diff_per_game = (form.goals_for - form.goals_against) / form.matches_considered
    return max(MIN_STRENGTH, points_per_game + goal_diff_per_game * 0.5)


def predict(
    home_form: FormReport,
    away_form: FormReport,
    h2h: H2HReport,
    home_squad: Optional[SquadReport] = None,
    away_squad: Optional[SquadReport] = None,
) -> Prediction:
    home_strength = _team_strength(home_form) + HOME_ADVANTAGE
    away_strength = _team_strength(away_form)

    rationale = []
    home_has_form_data = home_form.matches_considered > 0
    away_has_form_data = away_form.matches_considered > 0

    if home_has_form_data:
        rationale.append(
            f"{home_form.team.name} son {home_form.matches_considered} maç: "
            f"{home_form.wins}G {home_form.draws}B {home_form.losses}M "
            f"(form: {home_form.form_string or '-'})"
        )
    else:
        rationale.append(f"{home_form.team.name} için form verisi bulunamadı — VERİ YOK.")

    if away_has_form_data:
        rationale.append(
            f"{away_form.team.name} son {away_form.matches_considered} maç: "
            f"{away_form.wins}G {away_form.draws}B {away_form.losses}M "
            f"(form: {away_form.form_string or '-'})"
        )
    else:
        rationale.append(f"{away_form.team.name} için form verisi bulunamadı — VERİ YOK.")

    rationale.append("Ev sahibi avantajı hesaba katıldı.")

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

    if home_squad is not None and home_squad.impact_score > 0:
        home_strength -= home_squad.impact_score * SQUAD_IMPACT_WEIGHT
        rationale.append(
            f"{home_squad.team.name} kadro etkisi: {home_squad.impact_level} "
            f"({len(home_squad.missing_players)} eksik oyuncu)"
        )
    if away_squad is not None and away_squad.impact_score > 0:
        away_strength -= away_squad.impact_score * SQUAD_IMPACT_WEIGHT
        rationale.append(
            f"{away_squad.team.name} kadro etkisi: {away_squad.impact_level} "
            f"({len(away_squad.missing_players)} eksik oyuncu)"
        )

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

    if not home_has_form_data or not away_has_form_data:
        # En az bir takım için gerçek veri yok: nötr yer tutucu kullanıldığından
        # sonuç güvenilir bir istatistiğe dayanmıyor — bu açıkça belirtilmeli.
        confidence = "Yetersiz Veri"
        rationale.append(
            "UYARI: En az bir takım için form verisi bulunamadığından bu yüzdeler "
            "güvenilir bir istatistiğe dayanmıyor."
        )

    return Prediction(
        home=home_form.team,
        away=away_form.team,
        home_win_prob=home_win_prob,
        draw_prob=draw_prob,
        away_win_prob=away_win_prob,
        confidence=confidence,
        rationale=rationale,
    )
