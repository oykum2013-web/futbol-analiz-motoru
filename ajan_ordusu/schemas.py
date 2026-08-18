"""Ajanlar arasında paylaşılan veri şemaları.

Bu modül, ajan mimarisindeki her ajanın girdi/çıktı olarak kullandığı
ortak veri yapılarını tanımlar (bkz. proje brifi - "Ajanların veri
şemasını tasarla" adımı).
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TeamRef:
    """Bir takımı kimliklemek için minimal referans."""

    id: str
    name: str


@dataclass
class MatchResult:
    """Tamamlanmış (veya planlanmış) tek bir maçın normalize edilmiş hâli."""

    date: str  # ISO tarih (YYYY-MM-DD)
    home: TeamRef
    away: TeamRef
    home_goals: Optional[int]
    away_goals: Optional[int]
    competition: Optional[str] = None

    @property
    def is_finished(self) -> bool:
        return self.home_goals is not None and self.away_goals is not None


@dataclass
class FormReport:
    """Form Analiz Ajanı çıktısı: bir takımın son N maçtaki performansı."""

    team: TeamRef
    matches_considered: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    form_string: str  # en eski -> en yeni, örn. "GBGMG" (G/B/M)
    avg_goals_for: float
    avg_goals_against: float


@dataclass
class H2HReport:
    """Head-to-Head Ajanı çıktısı: iki takım arasındaki geçmiş karşılaşmalar."""

    home: TeamRef
    away: TeamRef
    matches_considered: int
    home_wins: int
    away_wins: int
    draws: int
    home_goals: int
    away_goals: int
    last_meetings: List[MatchResult] = field(default_factory=list)


@dataclass
class Prediction:
    """Tahmin Ajanı çıktısı: olasılık tabanlı maç sonucu tahmini."""

    home: TeamRef
    away: TeamRef
    home_win_prob: float
    draw_prob: float
    away_win_prob: float
    confidence: str  # "Düşük" | "Orta" | "Yüksek"
    rationale: List[str] = field(default_factory=list)
    disclaimer: str = (
        "Bu tahmin olasılık tabanlıdır ve kesin bir sonuç garantisi değildir. "
        "Bahis/yatırım kararı için tek başına kullanılmamalıdır."
    )
