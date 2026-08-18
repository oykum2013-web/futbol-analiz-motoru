"""Rapor & Bülten Ajanı.

Birden çok maçın analiz sonucunu (`orchestrator.MatchAnalysisReport`) günlük/
haftalık bir tahmin bültenine dönüştürür.

Her maç için:
- olasılıklar ve güven düzeyi,
- hangi verilerin eksik olduğu (form/H2H/kadro/oran) açıkça "VERİ YOK" /
  "Yetersiz Veri" olarak,
- ve risk uyarısı

net biçimde gösterilir. Bu ajan hiçbir eksik veriyi gizlemez ya da sayıyla
telafi etmez — sadece alttaki ajanların (form, H2H, kadro, piyasa, tahmin)
zaten ürettiği gerçek sonuçları/uyarıları biçimlendirir.
"""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .orchestrator import MatchAnalysisReport

RISK_WARNING = (
    "⚠️ RİSK UYARISI: Bu bültendeki hiçbir tahmin/oran kesin bir sonuç garantisi "
    "değildir. Sadece olasılık tabanlı bir analizdir; bahis/yatırım kararı için "
    "tek başına kullanılmamalıdır."
)

# Bu güven düzeylerinden biriyle gelen tahminler bültende ayrıca ⚠️ ile işaretlenir.
LOW_CONFIDENCE_LEVELS = {"Yetersiz Veri", "Çok Düşük"}


def _data_gaps(report: MatchAnalysisReport) -> List[str]:
    """Bu maç için hangi ajanların gerçek veri bulamadığını listeler (varsa)."""
    gaps: List[str] = []
    if report.home_form.matches_considered == 0:
        gaps.append(f"{report.home_form.team.name}: form verisi yok")
    if report.away_form.matches_considered == 0:
        gaps.append(f"{report.away_form.team.name}: form verisi yok")
    if report.h2h.matches_considered == 0:
        gaps.append("H2H verisi yok")
    if report.home_squad.impact_level == "Bilinmiyor":
        gaps.append(f"{report.home_squad.team.name}: kadro/sakatlık verisi yok")
    if report.away_squad.impact_level == "Bilinmiyor":
        gaps.append(f"{report.away_squad.team.name}: kadro/sakatlık verisi yok")
    if not report.market.data_available:
        gaps.append("Oran/piyasa verisi yok")
    if not report.standings.data_available:
        gaps.append("Puan durumu verisi yok")
    return gaps


def to_bulletin_dict(
    reports: List[MatchAnalysisReport],
    title: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Bültenin yapılandırılmış (JSON'a uygun) hâli — HTTP API için.

    Alttaki ajanların ürettiği gerçek verileri/uyarıları olduğu gibi taşır;
    `markdown` alanı, `format_bulletin_markdown` ile üretilen aynı metni içerir
    (n8n gibi araçların doğrudan bir dosyaya yazabilmesi için).
    """
    generated_at = generated_at or datetime.now(timezone.utc)
    return {
        "title": title or "Günlük Tahmin Bülteni",
        "generated_at": generated_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "risk_warning": RISK_WARNING,
        "match_count": len(reports),
        "matches": [
            {
                "home": asdict(report.prediction.home),
                "away": asdict(report.prediction.away),
                "form": {"home": asdict(report.home_form), "away": asdict(report.away_form)},
                "h2h": asdict(report.h2h),
                "squad": {"home": asdict(report.home_squad), "away": asdict(report.away_squad)},
                "market": asdict(report.market),
                "standings": asdict(report.standings),
                "prediction": asdict(report.prediction),
                "data_gaps": _data_gaps(report),
            }
            for report in reports
        ],
        "markdown": format_bulletin_markdown(reports, title=title, generated_at=generated_at),
    }


def format_bulletin_markdown(
    reports: List[MatchAnalysisReport],
    title: Optional[str] = None,
    generated_at: Optional[datetime] = None,
) -> str:
    """Tam Markdown bülten — rapor/e-posta/arşiv için."""
    generated_at = generated_at or datetime.now(timezone.utc)
    title = title or "Günlük Tahmin Bülteni"

    lines = [
        f"# {title}",
        f"_Oluşturulma zamanı: {generated_at.strftime('%Y-%m-%d %H:%M UTC')}_",
        "",
        f"> {RISK_WARNING}",
        "",
    ]

    if not reports:
        lines.append("Bu dönem için analiz edilecek maç bulunamadı.")
        return "\n".join(lines)

    lines.append(f"Toplam {len(reports)} maç analiz edildi.")
    lines.append("")

    for report in reports:
        p = report.prediction
        gaps = _data_gaps(report)
        low_conf = p.confidence in LOW_CONFIDENCE_LEVELS

        lines.append(f"## {p.home.name} vs {p.away.name}")
        if low_conf or gaps:
            lines.append(
                f"⚠️ **Dikkat ({p.confidence})** — bu tahmin, aşağıda listelenen eksik "
                "verilerden dolayı düşük güvenilirlikli olabilir."
            )
        lines.append(
            f"- Ev: %{p.home_win_prob} | Beraberlik: %{p.draw_prob} | Deplasman: %{p.away_win_prob} "
            f"| Güven: **{p.confidence}**"
        )
        lines.append("- Eksik veri: " + ("; ".join(gaps) if gaps else "yok (tüm kaynaklar sorgulandı)"))
        lines.append("")

    lines.append(f"> {RISK_WARNING}")
    return "\n".join(lines)


def format_bulletin_message(reports: List[MatchAnalysisReport], title: Optional[str] = None) -> str:
    """E-posta/Telegram gibi kısa mesaj kanalları için sade (tablosuz) özet."""
    title = title or "Günlük Tahmin Bülteni"
    lines = [f"📊 {title}", RISK_WARNING, ""]

    if not reports:
        lines.append("Bu dönem için analiz edilecek maç bulunamadı.")
        return "\n".join(lines)

    for report in reports:
        p = report.prediction
        gaps = _data_gaps(report)
        flag = " ⚠️" if (p.confidence in LOW_CONFIDENCE_LEVELS or gaps) else ""
        lines.append(
            f"⚽ {p.home.name} vs {p.away.name}{flag}\n"
            f"   Ev %{p.home_win_prob} · Berabere %{p.draw_prob} · Deplasman %{p.away_win_prob} "
            f"· Güven: {p.confidence}"
        )
        if gaps:
            lines.append(f"   Eksik veri: {', '.join(gaps)}")
        lines.append("")

    lines.append(RISK_WARNING)
    return "\n".join(lines)
