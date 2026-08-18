"""Genel amaçlı, Chromium tabanlı tarayıcı istemcisi (Playwright).

API'si olmayan ya da JavaScript ile render edilen herhangi bir web
sayfasından veri çekmek için kullanılır (ör. bir haber/hasar raporu
sayfası, JS ile yüklenen bir istatistik tablosu). `requests` tabanlı
diğer istemcilerin (football_data, the_odds_api, api_football) aksine
belirli bir API sözleşmesine bağlı değildir — verilen herhangi bir URL'e
gidip görünür metni veya tabloları döndürür.

`playwright` paketi zorunlu bir bağımlılık değildir (bkz. requirements.txt'de
opsiyonel not); bu modül import edildiğinde değil, gerçekten kullanılmaya
çalışıldığında (BrowserScraper.__enter__) hataya düşer, böylece playwright
kurulu olmayan ortamlarda geri kalan paket sorunsuz import edilebilir.
"""

from __future__ import annotations

import glob
import os
from typing import List, Optional


class BrowserScraperError(Exception):
    """playwright kurulu değil, tarayıcı başlatılamadı ya da sayfa yüklenemedi."""


def _find_preinstalled_chromium() -> Optional[str]:
    """`playwright install` çalıştırılmamış ama ortamda PLAYWRIGHT_BROWSERS_PATH altında
    önceden indirilmiş bir Chromium varsa (ör. bazı sandbox/CI imajları), yürütülebilir
    dosyasını bulur. pip'teki playwright paketinin beklediği build numarasıyla ortamdaki
    önceden-kurulmuş build birebir eşleşmeyebilir (bkz. proje geçmişi); bu durumda normal
    `chromium.launch()` "Executable doesn't exist" hatasıyla başarısız olur, biz de burada
    bulduğumuz herhangi bir Chromium ikili dosyasını `executable_path` olarak deneriz."""
    browsers_path = os.environ.get("PLAYWRIGHT_BROWSERS_PATH")
    if not browsers_path:
        return None
    patterns = [
        os.path.join(browsers_path, "chromium-*", "chrome-linux", "chrome"),
        os.path.join(browsers_path, "chromium-*", "chrome-mac", "*.app", "Contents", "MacOS", "*"),
        os.path.join(browsers_path, "chromium-*", "chrome-win", "chrome.exe"),
    ]
    for pattern in patterns:
        matches = sorted(glob.glob(pattern))
        if matches:
            return matches[-1]
    return None


class BrowserScraper:
    """Context manager: `with BrowserScraper() as scraper: scraper.fetch_text(url)`.

    Her `with` bloğu tek bir headless Chromium örneği açıp kapatır; birden
    çok URL aynı blok içinde ziyaret edilerek tarayıcı başlatma maliyeti
    tek seferde ödenir.
    """

    def __init__(self, timeout_ms: int = 15_000, headless: bool = True):
        self.timeout_ms = timeout_ms
        self.headless = headless
        self._playwright = None
        self._browser = None

    def __enter__(self) -> "BrowserScraper":
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise BrowserScraperError(
                "playwright kurulu değil. Kurulum için: pip install playwright && "
                "playwright install chromium"
            ) from exc

        self._playwright = sync_playwright().start()
        try:
            self._browser = self._playwright.chromium.launch(headless=self.headless)
        except Exception as exc:  # noqa: BLE001 - tarayıcı ikili dosyası eksik olabilir
            fallback_executable = _find_preinstalled_chromium()
            if fallback_executable is None:
                self._playwright.stop()
                self._playwright = None
                raise BrowserScraperError(f"Chromium başlatılamadı: {exc}") from exc
            try:
                self._browser = self._playwright.chromium.launch(
                    headless=self.headless, executable_path=fallback_executable
                )
            except Exception as fallback_exc:  # noqa: BLE001
                self._playwright.stop()
                self._playwright = None
                raise BrowserScraperError(
                    f"Chromium başlatılamadı (varsayılan hata: {exc}; "
                    f"önceden-kurulu '{fallback_executable}' ile de başarısız: {fallback_exc})"
                ) from fallback_exc
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._browser is not None:
            self._browser.close()
        if self._playwright is not None:
            self._playwright.stop()

    def _open_page(self, url: str, wait_selector: Optional[str]):
        if self._browser is None:
            raise BrowserScraperError("BrowserScraper 'with' bloğu dışında kullanılamaz")
        page = self._browser.new_page()
        try:
            page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")
            if wait_selector:
                page.wait_for_selector(wait_selector, timeout=self.timeout_ms)
        except Exception as exc:  # noqa: BLE001 - ağ/timeout hatalarını tek tip sarmalıyoruz
            page.close()
            raise BrowserScraperError(f"'{url}' yüklenemedi: {exc}") from exc
        return page

    def fetch_text(self, url: str, wait_selector: Optional[str] = None) -> str:
        """Sayfanın <body> içindeki görünür metnini döndürür (script/style hariç)."""
        page = self._open_page(url, wait_selector)
        try:
            return page.inner_text("body").strip()
        finally:
            page.close()

    def fetch_tables(self, url: str, wait_selector: Optional[str] = None) -> List[List[List[str]]]:
        """Sayfadaki her <table> için satır/hücre metinlerini döndürür.

        Dönüş: tablo listesi -> her tablo satır listesi -> her satır hücre metni listesi.
        """
        page = self._open_page(url, wait_selector)
        try:
            return page.eval_on_selector_all(
                "table",
                """
                (tables) => tables.map(table =>
                    Array.from(table.querySelectorAll('tr')).map(row =>
                        Array.from(row.querySelectorAll('th,td')).map(cell => cell.innerText.trim())
                    )
                )
                """,
            )
        finally:
            page.close()
