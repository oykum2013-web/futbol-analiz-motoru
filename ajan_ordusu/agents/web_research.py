"""Web Araştırma Ajanı.

Kullanıcının verdiği herhangi bir URL'yi (Chromium/Playwright ile, JS
render dahil) ziyaret edip ham, görünür metni toplar. Diğer ajanların
aksine (form, H2H, kadro, piyasa) sabit bir API şemasına bağlı değildir;
bu yüzden çıktısı **yapılandırılmış bir olasılık/istatistik değil, ham
kaynak metnidir** ve tahmin motoruna (prediction.py) dahil edilmez.

Veri bütünlüğü kuralı burada da geçerlidir: bir URL'e erişilemezse
sessizce atlanmaz, "erişilemedi" olarak açıkça raporlanır.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional

from ..clients.browser_scraper import BrowserScraper, BrowserScraperError

MAX_SNIPPET_CHARS = 2000


@dataclass
class WebSnippet:
    url: str
    fetched_at: str
    text: Optional[str] = None
    error: Optional[str] = None


def gather_web_snippets(urls: List[str], wait_selector: Optional[str] = None) -> List[WebSnippet]:
    """Verilen URL'leri tek bir tarayıcı oturumunda gezip metinlerini toplar.

    playwright kurulu değilse ya da tarayıcı hiç başlatılamazsa, TÜM URL'ler
    için tek bir ortak hata mesajıyla WebSnippet listesi döner (pipeline'ın
    geri kalanını çökertmez).
    """
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        with BrowserScraper() as scraper:
            snippets = []
            for url in urls:
                try:
                    text = scraper.fetch_text(url, wait_selector=wait_selector)
                    snippets.append(WebSnippet(url=url, fetched_at=now, text=text[:MAX_SNIPPET_CHARS]))
                except BrowserScraperError as exc:
                    snippets.append(WebSnippet(url=url, fetched_at=now, error=str(exc)))
            return snippets
    except BrowserScraperError as exc:
        return [WebSnippet(url=url, fetched_at=now, error=str(exc)) for url in urls]


def format_web_research_markdown(snippets: List[WebSnippet]) -> str:
    if not snippets:
        return ""

    lines = [
        "## Web Araştırma (Ham, Doğrulanmamış)",
        "> ⚠️ Bu bölüm Chromium ile ziyaret edilen sayfalardan alınan HAM metindir. "
        "Yukarıdaki tahmine dahil edilmemiştir; sadece ek bağlam/manuel değerlendirme içindir.",
        "",
    ]
    for snip in snippets:
        lines.append(f"### {snip.url}")
        lines.append(f"_Erişim: {snip.fetched_at}_")
        if snip.error:
            lines.append(f"**ERİŞİLEMEDİ:** {snip.error}")
        else:
            lines.append("")
            lines.append(snip.text or "_(boş sayfa)_")
        lines.append("")
    return "\n".join(lines)
