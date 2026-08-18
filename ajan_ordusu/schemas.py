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
class PlayerRef:
    """Bir oyuncuyu kimliklemek için minimal referans."""

    id: str
    name: str
    position: Optional[str] = None


@dataclass
class InjuryEntry:
    """Sakat/cezalı/eksik tek bir oyuncu kaydı."""

    player: PlayerRef
    reason: str  # örn. "Sakatlık", "Cezalı", "Kadro Dışı"
    # Oyuncunun takım için önemi (1.0 = normal, >1.0 = kilit oyuncu). Veri yoksa 1.0 varsayılır.
    importance: float = 1.0


@dataclass
class SquadReport:
    """Sakatlık/Kadro Ajanı çıktısı: eksik oyuncuların takım gücüne etkisi."""

    team: TeamRef
    missing_players: List[InjuryEntry] = field(default_factory=list)
    impact_score: float = 0.0  # 0.0 (etkisiz) .. 1.0 (çok yüksek etki)
    impact_level: str = "Yok"  # "Yok" | "Düşük" | "Orta" | "Yüksek"
    notes: List[str] = field(default_factory=list)


@dataclass
class OddsQuote:
    """Tek bir bahis şirketinin bir maç için verdiği gerçek ondalık oranlar."""

    bookmaker: str
    home_odds: Optional[float] = None
    draw_odds: Optional[float] = None
    away_odds: Optional[float] = None


@dataclass
class MarketReport:
    """Oran/Piyasa Ajanı çıktısı: gerçek bahis oranlarından hesaplanan zımni olasılıklar."""

    home: TeamRef
    away: TeamRef
    data_available: bool = False
    quotes: List[OddsQuote] = field(default_factory=list)
    # Vig (bahis şirketi marjı) arındırılmış, bahis şirketleri arası ortalama zımni olasılıklar (0..100).
    consensus_home_prob: Optional[float] = None
    consensus_draw_prob: Optional[float] = None
    consensus_away_prob: Optional[float] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class StandingsEntry:
    """Puan Durumu Ajanı girdisi: bir takımın lig tablosundaki güncel satırı."""

    team: TeamRef
    position: int
    played: int
    won: int
    draw: int
    lost: int
    goals_for: int
    goals_against: int
    points: int


@dataclass
class StandingsReport:
    """Puan Durumu Ajanı çıktısı: iki takımın lig tablosundaki konumu/performansı."""

    home: TeamRef
    away: TeamRef
    data_available: bool = False
    home_entry: Optional[StandingsEntry] = None
    away_entry: Optional[StandingsEntry] = None
    notes: List[str] = field(default_factory=list)


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
