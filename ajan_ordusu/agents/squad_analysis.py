"""Sakatlık / Kadro Ajanı.

Eksik (sakat/cezalı/kadro dışı) oyuncuları değerlendirip bunun takım gücüne
olası etkisini basit, açıklanabilir bir skora dönüştürür.

ÖNEMLİ (veri bütünlüğü kuralı): Bu ajan hiçbir zaman sahte/uydurma sakatlık
verisi üretmez. `missing_players=None` ("veri hiç sorgulanamadı/alınamadı")
ile `missing_players=[]` ("kaynak sorgulandı, bilinen bir eksik yok") kesin
olarak birbirinden ayrılır — aksi hâlde "veri yok" durumu "kadro tam" gibi
yanlış yorumlanabilir.
"""

from typing import Any, Dict, List, Optional

from .. import config
from ..schemas import InjuryEntry, PlayerRef, SquadReport, TeamRef


def normalize_api_football_injuries(raw_injuries: List[Dict[str, Any]]) -> List[InjuryEntry]:
    """API-Football /injuries çıktısını normalize eder."""
    normalized = []
    for entry in raw_injuries:
        player = entry.get("player", {}) or {}
        normalized.append(
            InjuryEntry(
                player=PlayerRef(
                    id=str(player.get("id")),
                    name=player.get("name") or "?",
                    position=player.get("type"),  # API-Football burada mevki yerine sakatlık tipini de koyabilir
                ),
                reason=player.get("reason") or "Belirtilmemiş",
            )
        )
    return normalized


def analyze_squad(
    team: TeamRef,
    missing_players: Optional[List[InjuryEntry]] = None,
    impact_scale: float = config.SQUAD_IMPACT_SCALE,
) -> SquadReport:
    """`missing_players=None` ile `missing_players=[]` farklı anlamlara gelir:

    - `None`: kaynak hiç sorgulanamadı (API anahtarı yok, istek başarısız vb.) → durum "Bilinmiyor".
    - `[]`: kaynak başarıyla sorgulandı ve bilinen eksik oyuncu yok → etki "Yok" (doğrulanmış).
    - dolu liste: gerçek kaynaktan gelen eksik oyuncular değerlendirilir.
    """
    if missing_players is None:
        return SquadReport(
            team=team,
            missing_players=[],
            impact_score=0.0,
            impact_level="Bilinmiyor",
            notes=["Sakatlık/kadro verisi alınamadı (kaynak sorgulanmadı ya da erişilemedi) — veri yok."],
        )

    if not missing_players:
        return SquadReport(
            team=team,
            missing_players=[],
            impact_score=0.0,
            impact_level="Yok",
            notes=["Kaynak sorgulandı: bilinen bir eksik oyuncu yok."],
        )

    weighted_count = sum(entry.importance for entry in missing_players)
    impact_score = round(min(1.0, impact_scale * weighted_count), 2)

    if impact_score == 0.0:
        impact_level = "Yok"
    elif impact_score < 0.25:
        impact_level = "Düşük"
    elif impact_score < 0.55:
        impact_level = "Orta"
    else:
        impact_level = "Yüksek"

    notes = [
        f"{len(missing_players)} oyuncu eksik: "
        + ", ".join(f"{e.player.name} ({e.reason})" for e in missing_players[:5])
        + (" ..." if len(missing_players) > 5 else "")
    ]

    return SquadReport(
        team=team,
        missing_players=missing_players,
        impact_score=impact_score,
        impact_level=impact_level,
        notes=notes,
    )
