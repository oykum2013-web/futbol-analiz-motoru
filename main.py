"""
GPR Radar - Tork Pro 300
Farmet Teknoloji GPR Analiz Uygulaması

Ana giriş noktası.
"""

import logging
import sys

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from gpr_radar.ui.main_window import MainWindow


def setup_logging() -> None:
    """Loglama yapılandırması."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("gpr_radar.log", encoding="utf-8"),
        ],
    )


def main() -> None:
    """Ana uygulama fonksiyonu."""
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("GPR Radar uygulaması başlatılıyor...")

    # Yüksek DPI desteği
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("GPR Radar - Tork Pro 300")
    app.setOrganizationName("Farmet Teknoloji")
    app.setApplicationVersion("1.0.0")

    # Koyu tema stil sayfası
    app.setStyleSheet(
        """
        QMainWindow {
            background-color: #1e1e2e;
        }
        QWidget {
            background-color: #1e1e2e;
            color: #cdd6f4;
            font-size: 12px;
        }
        QGroupBox {
            border: 1px solid #45475a;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 15px;
            font-weight: bold;
            color: #89b4fa;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px;
        }
        QPushButton {
            background-color: #45475a;
            color: #cdd6f4;
            border: 1px solid #585b70;
            border-radius: 4px;
            padding: 5px 15px;
            min-height: 25px;
        }
        QPushButton:hover {
            background-color: #585b70;
        }
        QPushButton:pressed {
            background-color: #313244;
        }
        QPushButton:disabled {
            background-color: #313244;
            color: #585b70;
        }
        QComboBox {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 4px;
            padding: 3px 8px;
            min-height: 22px;
        }
        QComboBox::drop-down {
            border: none;
        }
        QComboBox QAbstractItemView {
            background-color: #313244;
            color: #cdd6f4;
            selection-background-color: #45475a;
        }
        QSpinBox, QDoubleSpinBox {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 4px;
            padding: 3px;
        }
        QSlider::groove:horizontal {
            height: 6px;
            background-color: #313244;
            border-radius: 3px;
        }
        QSlider::handle:horizontal {
            width: 16px;
            height: 16px;
            margin: -5px 0;
            background-color: #89b4fa;
            border-radius: 8px;
        }
        QSlider::sub-page:horizontal {
            background-color: #89b4fa;
            border-radius: 3px;
        }
        QCheckBox {
            spacing: 8px;
            color: #cdd6f4;
        }
        QCheckBox::indicator {
            width: 16px;
            height: 16px;
            border: 1px solid #45475a;
            border-radius: 3px;
            background-color: #313244;
        }
        QCheckBox::indicator:checked {
            background-color: #89b4fa;
        }
        QLabel {
            color: #cdd6f4;
        }
        QTextEdit {
            background-color: #313244;
            color: #cdd6f4;
            border: 1px solid #45475a;
            border-radius: 4px;
        }
        QMenuBar {
            background-color: #181825;
            color: #cdd6f4;
        }
        QMenuBar::item:selected {
            background-color: #313244;
        }
        QMenu {
            background-color: #1e1e2e;
            color: #cdd6f4;
            border: 1px solid #45475a;
        }
        QMenu::item:selected {
            background-color: #313244;
        }
        QToolBar {
            background-color: #181825;
            border-bottom: 1px solid #313244;
            spacing: 5px;
            padding: 3px;
        }
        QStatusBar {
            background-color: #181825;
            color: #a6adc8;
        }
        QScrollArea {
            border: none;
        }
        QTabWidget::pane {
            border: 1px solid #45475a;
            background-color: #1e1e2e;
        }
        QTabBar::tab {
            background-color: #313244;
            color: #cdd6f4;
            padding: 5px 15px;
            border: 1px solid #45475a;
            border-bottom: none;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #1e1e2e;
            color: #89b4fa;
        }
        QSplitter::handle {
            background-color: #45475a;
            height: 3px;
        }
    """
    )

    window = MainWindow()
    window.show()

    logger.info("Uygulama başlatıldı")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
