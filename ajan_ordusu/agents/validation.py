"""Doğrulama / Hata Kontrol Ajanı.

Diğer ajanların (özellikle Tahmin Ajanı) ürettiği çıktıyı iç tutarlılık
hataları için denetler:

- Olasılık toplamı 100'den sapmışsa (yuvarlama zinciri kaynaklı küçük bir
  fark ise) otomatik düzeltir; sapma büyükse (muhtemel bir kod hatası)
  otomatik düzeltmeyi reddedip AÇIKÇA "DÜZELTİLEMEDİ" olarak işaretler.
- Olasılıkların 0-100 aralığında olduğunu doğrular.
- Güven düzeyinin eldeki veriyle çeliştiği durumları (ör. form verisi yokken
  yüksek güven gösterilmesi) yakalayıp düzeltir.

Veri bütünlüğü kuralı burada da geçerlidir: bu ajan asla bir hatayı sessizce
yutup "her şey yolunda" görüntüsü vermez — düzeltemediği her şeyi rapora
açıkça yazar.
"""

from dataclasses import dataclass, field
from typing import List

from ..schemas import FormReport, Prediction

# Yuvarlama zincirinden (birden çok round() çağrısı üst üste) kaynaklanabilecek
# makul sapma sınırı. Bunun üzerindeki bir fark artık "yuvarlama" değil, olası
# bir hesaplama hatasıdır — otomatik düzeltilmez, açıkça raporlanır.
PROB_SUM_AUTOFIX_TOLERANCE = 0.5


@dataclass
class ValidationResult:
    fixed: List[str] = field(default_factory=list)
    unresolved: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.unresolved


def _fix_probability_sum(p: Prediction, result: ValidationResult) -> None:
    total = round(p.home_win_prob + p.draw_prob + p.away_win_prob, 2)
    diff = round(100 - total, 2)
    if abs(diff) < 0.05:
        return
    if abs(diff) > PROB_SUM_AUTOFIX_TOLERANCE:
        result.unresolved.append(
            f"Olasılık toplamı %100 yerine %{total} — fark (%{diff:+}) yuvarlama ile "
            "açıklanamayacak kadar büyük, otomatik düzeltme yapılmadı."
        )
        return
    largest_field = max(
        ("home_win_prob", p.home_win_prob),
        ("draw_prob", p.draw_prob),
        ("away_win_prob", p.away_win_prob),
        key=lambda item: item[1],
    )[0]
    setattr(p, largest_field, round(getattr(p, largest_field) + diff, 1))
    result.fixed.append(
        f"Olasılık toplamı %{total} idi (100 olmalıydı); yuvarlama farkı (%{diff:+}) "
        f"en büyük paya ({largest_field}) eklenerek düzeltildi."
    )


def _check_probability_ranges(p: Prediction, result: ValidationResult) -> None:
    for name in ("home_win_prob", "draw_prob", "away_win_prob"):
        value = getattr(p, name)
        if value < 0 or value > 100:
            result.unresolved.append(
                f"{name} aralık dışı bir değer taşıyor ({value}, 0-100 arası olmalı) — "
                "otomatik düzeltilemedi, ajan kodunda hata olabilir."
            )


def _fix_confidence_consistency(
    home_form: FormReport, away_form: FormReport, p: Prediction, result: ValidationResult
) -> None:
    missing_data = home_form.matches_considered == 0 or away_form.matches_considered == 0
    if missing_data and p.confidence != "Yetersiz Veri":
        old = p.confidence
        p.confidence = "Yetersiz Veri"
        result.fixed.append(
            f"En az bir takım için form verisi yokken güven düzeyi '{old}' olarak işaretlenmişti — "
            "'Yetersiz Veri' olarak düzeltildi."
        )


def validate_and_fix(home_form: FormReport, away_form: FormReport, prediction: Prediction) -> ValidationResult:
    """Tahmini denetler, güvenle düzeltilebilecek hataları düzeltir, kalanları işaretler."""
    result = ValidationResult()
    _fix_probability_sum(prediction, result)
    _check_probability_ranges(prediction, result)
    _fix_confidence_consistency(home_form, away_form, prediction, result)
    return result


def format_validation_markdown(result: ValidationResult) -> str:
    if not result.fixed and not result.unresolved:
        return "## Doğrulama / Hata Kontrolü\n- ✅ Hata bulunmadı, rapor iç tutarlılık kontrolünden geçti."

    lines = ["## Doğrulama / Hata Kontrolü"]
    for msg in result.fixed:
        lines.append(f"- ✅ Düzeltildi: {msg}")
    for msg in result.unresolved:
        lines.append(f"- ❌ DÜZELTİLEMEDİ: {msg}")
    return "\n".join(lines)
