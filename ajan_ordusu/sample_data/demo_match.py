"""Uçtan uca prototipi ağ/anahtar gerektirmeden çalıştırmak için örnek veri.

DİKKAT: Takım adları ve maç sonuçları tamamen kurgusaldır, gerçek bir takımı
veya maç sonucunu temsil etmez. Sadece pipeline'ı test etmek içindir.
"""

from ..schemas import InjuryEntry, MatchResult, PlayerRef, TeamRef

TAKIM_A = TeamRef(id="demo-a", name="Yıldız Spor (DEMO)")
TAKIM_B = TeamRef(id="demo-b", name="Deniz Yıldızı FK (DEMO)")
TAKIM_C = TeamRef(id="demo-c", name="Kartal Gençlik (DEMO)")
TAKIM_D = TeamRef(id="demo-d", name="Orman Birlik (DEMO)")

# Takım A'nın son maçları (en yeni önce)
TAKIM_A_SON_MACLAR = [
    MatchResult("2026-08-10", TAKIM_A, TAKIM_C, 2, 1, "Demo Lig"),
    MatchResult("2026-08-03", TAKIM_D, TAKIM_A, 0, 0, "Demo Lig"),
    MatchResult("2026-07-27", TAKIM_A, TAKIM_D, 3, 1, "Demo Lig"),
    MatchResult("2026-07-20", TAKIM_C, TAKIM_A, 1, 2, "Demo Lig"),
    MatchResult("2026-07-13", TAKIM_A, TAKIM_B, 1, 1, "Demo Lig"),
]

# Takım B'nin son maçları (en yeni önce)
TAKIM_B_SON_MACLAR = [
    MatchResult("2026-08-09", TAKIM_B, TAKIM_D, 1, 0, "Demo Lig"),
    MatchResult("2026-08-02", TAKIM_C, TAKIM_B, 2, 2, "Demo Lig"),
    MatchResult("2026-07-26", TAKIM_B, TAKIM_C, 0, 1, "Demo Lig"),
    MatchResult("2026-07-19", TAKIM_D, TAKIM_B, 1, 3, "Demo Lig"),
    MatchResult("2026-07-13", TAKIM_A, TAKIM_B, 1, 1, "Demo Lig"),
]

# A ile B arasındaki geçmiş karşılaşmalar (en yeni önce)
H2H_MACLAR = [
    MatchResult("2026-07-13", TAKIM_A, TAKIM_B, 1, 1, "Demo Lig"),
    MatchResult("2026-02-02", TAKIM_B, TAKIM_A, 0, 2, "Demo Lig"),
    MatchResult("2025-11-15", TAKIM_A, TAKIM_B, 2, 0, "Demo Lig"),
    MatchResult("2025-04-06", TAKIM_B, TAKIM_A, 1, 1, "Demo Lig"),
]

# Takım A'nın eksik oyuncuları (kurgusal) — biri kilit oyuncu (importance=2.0)
TAKIM_A_EKSIKLER = [
    InjuryEntry(PlayerRef(id="p1", name="O. Kurgusal", position="Forvet"), "Sakatlık", importance=2.0),
    InjuryEntry(PlayerRef(id="p2", name="B. Örnekoğlu", position="Defans"), "Cezalı", importance=1.0),
]

# Takım B'nin eksik oyuncuları (kurgusal) — kadro derinliği daha az etkilenmiş
TAKIM_B_EKSIKLER: list = []
