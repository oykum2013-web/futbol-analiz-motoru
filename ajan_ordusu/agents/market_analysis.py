"""Oran / Piyasa Ajanı.

Gerçek bahis şirketi oranlarından piyasanın zımni (implied) olasılıklarını
hesaplar. Bu hesap, gerçek oranlar üzerinde basit aritmetik (1/oran, vig
arındırma, ortalama) yapar — hiçbir sayı uydurmaz.

ÖNEMLİ (veri bütünlüğü kuralı): Bir maç için gerçek oran verisi
bulunamazsa (kaynak sorgulanamadı, bu maç için bahis şirketi verisi yoksa,
ya da bulunan oranlardan geçerli bir olasılık hesaplanamıyorsa),
`data_available=False` ile açıkça "veri yok" döner — asla rastgele/varsayılan
bir oran üretmez.
"""

from typing import Any, Dict, List, Optional, Tuple

from ..schemas import MarketReport, OddsQuote, TeamRef


def normalize_the_odds_api_event(raw_event: Dict[str, Any]) -> List[OddsQuote]:
    """The Odds API /v4/sports/{sport}/odds çıktısındaki tek bir maçı normalize eder."""
    home_name = raw_event.get("home_team")
    away_name = raw_event.get("away_team")

    quotes: List[OddsQuote] = []
    for bookmaker in raw_event.get("bookmakers", []) or []:
        h2h_market = next(
            (m for m in (bookmaker.get("markets") or []) if m.get("key") == "h2h"), None
        )
        if not h2h_market:
            continue

        home_odds = draw_odds = away_odds = None
        for outcome in h2h_market.get("outcomes", []) or []:
            name = outcome.get("name")
            price = outcome.get("price")
            if name == home_name:
                home_odds = price
            elif name == away_name:
                away_odds = price
            elif isinstance(name, str) and name.lower() == "draw":
                draw_odds = price

        if home_odds and away_odds:
            quotes.append(
                OddsQuote(
                    bookmaker=bookmaker.get("title") or bookmaker.get("key") or "?",
                    home_odds=home_odds,
                    draw_odds=draw_odds,
                    away_odds=away_odds,
                )
            )
    return quotes


def _devigged_probs(quote: OddsQuote) -> Optional[Tuple[float, float, float]]:
    """Tek bir bahis şirketinin oranlarından, marjı (vig) arındırılmış olasılıkları hesaplar."""
    if not quote.home_odds or not quote.away_odds:
        return None
    home_p = 1 / quote.home_odds
    away_p = 1 / quote.away_odds
    draw_p = 1 / quote.draw_odds if quote.draw_odds else 0.0
    overround = home_p + draw_p + away_p
    if overround <= 0:
        return None
    return home_p / overround, draw_p / overround, away_p / overround


def analyze_market(
    home: TeamRef, away: TeamRef, quotes: Optional[List[OddsQuote]] = None
) -> MarketReport:
    """`quotes=None` veya boş liste: bu maç için gerçek oran verisi bulunamadı."""
    if not quotes:
        return MarketReport(
            home=home,
            away=away,
            data_available=False,
            quotes=[],
            notes=[
                "Oran verisi bulunamadı (kaynak sorgulanmadı ya da bu maç için "
                "bahis şirketi verisi yok) — VERİ YOK."
            ],
        )

    devigged = [p for p in (_devigged_probs(q) for q in quotes) if p is not None]
    if not devigged:
        return MarketReport(
            home=home,
            away=away,
            data_available=False,
            quotes=quotes,
            notes=["Bulunan oranlardan geçerli bir olasılık hesaplanamadı — VERİ YOK."],
        )

    n = len(devigged)
    avg_home = sum(p[0] for p in devigged) / n
    avg_draw = sum(p[1] for p in devigged) / n
    avg_away = sum(p[2] for p in devigged) / n

    return MarketReport(
        home=home,
        away=away,
        data_available=True,
        quotes=quotes,
        consensus_home_prob=round(avg_home * 100, 1),
        consensus_draw_prob=round(avg_draw * 100, 1),
        consensus_away_prob=round(avg_away * 100, 1),
        notes=[f"{n} bahis şirketinden alınan gerçek oranların (vig arındırılmış) ortalaması."],
    )
