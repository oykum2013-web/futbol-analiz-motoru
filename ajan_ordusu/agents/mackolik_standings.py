"""Mackolik Puan Durumu Ajanı.

mackolik.com'un puan durumu sayfasındaki HTML tablosunu (Chromium/Playwright
ile, bkz. clients/browser_scraper.py) gerçek, yapılandırılmış `StandingsEntry`
kayıtlarına dönüştürür. football-data.org'un ücretsiz planında Türkiye Süper
Lig (TSL) desteklenmediği için (canlı API'ye karşı doğrulandı — 403 döner),
bu ajan Türkiye ligleri için API anahtarı gerektirmeyen alternatif bir
gerçek veri kaynağıdır.

Sütun sırası, mackolik'in Süper Lig puan durumu sayfasından gerçekten
çekilmiş ham `fetch_tables()` çıktısına bakılarak doğrulanmıştır (bkz. proje
geçmişi): ['#', '', 'TAKIM', 'O', '+/-', 'G', 'B', 'M', 'A', 'Y', 'AV', 'P'].
'+/-' sütunu 'AV' ile aynı değeri taşır (muhtemelen responsive tasarımın
mobilde gizlenen bir sütunu — DOM'dan yine de okunuyor) ve kullanılmaz.

mackolik takımları için football-data.org tarzı sayısal bir kimlik yok; bu
yüzden `TeamRef.id` olarak takımın tam adı kullanılır (mackolik tablosundaki
adla birebir aynı yazılmalı — eşleştirme tam metin karşılaştırmasıyla yapılır).

Veri bütünlüğü kuralı burada da geçerlidir: bir satır beklenen sütun sayısına
sahip değilse ya da sayısal alanlar parse edilemiyorsa, o satır sessizce
uydurma bir değerle doldurulmaz — atlanır (bkz. `parse_mackolik_standings_rows`).
"""

from __future__ import annotations

from typing import List

from ..clients.browser_scraper import BrowserScraper, BrowserScraperError
from ..schemas import StandingsEntry, TeamRef

# fetch_tables() çıktısındaki sütun indeksleri (bkz. modül docstring'i).
_COL_POSITION = 0
_COL_TEAM = 2
_COL_PLAYED = 3
_COL_WON = 5
_COL_DRAW = 6
_COL_LOST = 7
_COL_GOALS_FOR = 8
_COL_GOALS_AGAINST = 9
_COL_POINTS = 11
_MIN_COLUMNS = 12


class MackolikStandingsError(Exception):
    """Sayfa çekilemedi ya da beklenen tablo yapısı bulunamadı."""


def parse_mackolik_standings_rows(rows: List[List[str]]) -> List[StandingsEntry]:
    """`fetch_tables()`'ın tek bir tablosunun ham satırlarını `StandingsEntry` listesine çevirir.

    Başlık satırı ve sütun sayısı yetersiz/sayısal olmayan satırlar sessizce atlanır
    (uydurma veriyle doldurulmaz) — böylece sayfa yapısı hafifçe değişse bile pipeline
    çökmez, sadece o satır eksik kalır.
    """
    entries: List[StandingsEntry] = []
    for row in rows:
        if len(row) < _MIN_COLUMNS:
            continue
        try:
            position = int(row[_COL_POSITION])
            played = int(row[_COL_PLAYED])
            won = int(row[_COL_WON])
            draw = int(row[_COL_DRAW])
            lost = int(row[_COL_LOST])
            goals_for = int(row[_COL_GOALS_FOR])
            goals_against = int(row[_COL_GOALS_AGAINST])
            points = int(row[_COL_POINTS])
        except (ValueError, IndexError):
            continue  # başlık satırı ya da beklenmeyen bir satır — atla.

        team_name = row[_COL_TEAM].strip()
        if not team_name:
            continue

        entries.append(
            StandingsEntry(
                team=TeamRef(id=team_name, name=team_name),
                position=position,
                played=played,
                won=won,
                draw=draw,
                lost=lost,
                goals_for=goals_for,
                goals_against=goals_against,
                points=points,
            )
        )
    return entries


def fetch_mackolik_standings(url: str, wait_selector: str = "table") -> List[StandingsEntry]:
    """Verilen mackolik puan durumu URL'sini Chromium ile ziyaret edip parse eder.

    Sayfa hiç yüklenemezse ya da hiç tablo bulunamazsa `MackolikStandingsError`
    fırlatılır — sessizce boş/uydurma bir sonuç dönülmez (veri bütünlüğü kuralı).
    """
    try:
        with BrowserScraper() as scraper:
            tables = scraper.fetch_tables(url, wait_selector=wait_selector)
    except BrowserScraperError as exc:
        raise MackolikStandingsError(f"'{url}' çekilemedi: {exc}") from exc

    if not tables:
        raise MackolikStandingsError(f"'{url}' sayfasında hiç tablo bulunamadı.")

    entries = parse_mackolik_standings_rows(tables[0])
    if not entries:
        raise MackolikStandingsError(
            f"'{url}' sayfasındaki tablo bulundu ama beklenen puan durumu yapısına "
            "uymuyor (sütun sayısı/sırası değişmiş olabilir) — hiç satır parse edilemedi."
        )
    return entries


def format_mackolik_standings_markdown(entries: List[StandingsEntry], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        f"> Kaynak: mackolik.com (Chromium/Playwright ile çekildi, {len(entries)} takım).",
        "",
        "| # | Takım | O | G | B | M | A | Y | AV | P |",
        "|---|-------|---|---|---|---|---|---|----|----|",
    ]
    for e in sorted(entries, key=lambda x: x.position):
        diff = e.goals_for - e.goals_against
        lines.append(
            f"| {e.position} | {e.team.name} | {e.played} | {e.won} | {e.draw} | {e.lost} | "
            f"{e.goals_for} | {e.goals_against} | {diff:+d} | {e.points} |"
        )
    return "\n".join(lines)
