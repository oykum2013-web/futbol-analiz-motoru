"""
GPR Radar Kontrol Paneli
Cihaz ayarları, sinyal işleme parametreleri ve tarama kontrolü.
"""

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class DevicePanel(QGroupBox):
    """Cihaz bağlantı ve kontrol paneli."""

    connect_clicked = pyqtSignal(str, int)  # port, baud_rate
    disconnect_clicked = pyqtSignal()
    scan_start_clicked = pyqtSignal()
    scan_stop_clicked = pyqtSignal()
    simulate_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Cihaz Bağlantısı", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Port seçimi
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Port:"))
        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)
        self.port_combo.addItem("Simülasyon")
        port_layout.addWidget(self.port_combo)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedWidth(30)
        port_layout.addWidget(self.refresh_btn)
        layout.addLayout(port_layout)

        # Baud rate
        baud_layout = QHBoxLayout()
        baud_layout.addWidget(QLabel("Baud:"))
        self.baud_combo = QComboBox()
        for rate in [9600, 19200, 38400, 57600, 115200, 230400, 460800, 921600]:
            self.baud_combo.addItem(str(rate))
        self.baud_combo.setCurrentText("115200")
        baud_layout.addWidget(self.baud_combo)
        layout.addLayout(baud_layout)

        # Bağlan/Kes butonları
        btn_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Bağlan")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; color: white;")
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Bağlantıyı Kes")
        self.disconnect_btn.setStyleSheet("background-color: #f44336; color: white;")
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self.disconnect_clicked.emit)
        btn_layout.addWidget(self.disconnect_btn)
        layout.addLayout(btn_layout)

        # Tarama kontrol
        scan_layout = QHBoxLayout()
        self.start_scan_btn = QPushButton("▶ Taramayı Başlat")
        self.start_scan_btn.setStyleSheet(
            "background-color: #2196F3; color: white; font-weight: bold;"
        )
        self.start_scan_btn.setEnabled(False)
        self.start_scan_btn.clicked.connect(self.scan_start_clicked.emit)
        scan_layout.addWidget(self.start_scan_btn)

        self.stop_scan_btn = QPushButton("■ Durdur")
        self.stop_scan_btn.setStyleSheet("background-color: #FF9800; color: white;")
        self.stop_scan_btn.setEnabled(False)
        self.stop_scan_btn.clicked.connect(self.scan_stop_clicked.emit)
        scan_layout.addWidget(self.stop_scan_btn)
        layout.addLayout(scan_layout)

        # Durum göstergesi
        self.status_label = QLabel("Durum: Bağlı Değil")
        self.status_label.setStyleSheet("color: #888; font-weight: bold;")
        layout.addWidget(self.status_label)

        # Cihaz bilgileri
        self.info_label = QLabel("Batarya: -- | Sıcaklık: --")
        self.info_label.setStyleSheet("color: #666; font-size: 10px;")
        layout.addWidget(self.info_label)

    def _on_connect(self) -> None:
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())
        if port == "Simülasyon":
            self.simulate_clicked.emit()
        else:
            self.connect_clicked.emit(port, baud)

    def set_connected(self, connected: bool) -> None:
        """Bağlantı durumunu günceller."""
        self.connect_btn.setEnabled(not connected)
        self.disconnect_btn.setEnabled(connected)
        self.start_scan_btn.setEnabled(connected)
        self.port_combo.setEnabled(not connected)
        self.baud_combo.setEnabled(not connected)

    def set_scanning(self, scanning: bool) -> None:
        """Tarama durumunu günceller."""
        self.start_scan_btn.setEnabled(not scanning)
        self.stop_scan_btn.setEnabled(scanning)
        self.disconnect_btn.setEnabled(not scanning)

    def update_status(self, status: str) -> None:
        """Durum metnini günceller."""
        self.status_label.setText(f"Durum: {status}")

    def update_device_info(self, battery: float, temperature: float) -> None:
        """Cihaz bilgilerini günceller."""
        self.info_label.setText(
            f"Batarya: {battery:.0f}% | Sıcaklık: {temperature:.1f}°C"
        )

    def update_ports(self, ports: list[dict[str, str]]) -> None:
        """Port listesini günceller."""
        current = self.port_combo.currentText()
        self.port_combo.clear()
        self.port_combo.addItem("Simülasyon")
        for port in ports:
            self.port_combo.addItem(f"{port['port']} - {port['description']}")
        idx = self.port_combo.findText(current)
        if idx >= 0:
            self.port_combo.setCurrentIndex(idx)


class ProcessingPanel(QGroupBox):
    """Sinyal işleme parametreleri paneli."""

    params_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Sinyal İşleme", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Toprak Ayarı
        gb_group = QGroupBox("Otomatik Toprak Ayarı")
        gb_layout = QVBoxLayout(gb_group)

        self.ground_balance_check = QCheckBox("Toprak Ayarı Aktif")
        self.ground_balance_check.setChecked(True)
        self.ground_balance_check.stateChanged.connect(self.params_changed.emit)
        gb_layout.addWidget(self.ground_balance_check)

        self.calibrate_btn = QPushButton("Kalibrasyon Yap")
        self.calibrate_btn.setStyleSheet("background-color: #9C27B0; color: white;")
        gb_layout.addWidget(self.calibrate_btn)

        adapt_layout = QHBoxLayout()
        adapt_layout.addWidget(QLabel("Adaptasyon:"))
        self.adapt_rate_spin = QDoubleSpinBox()
        self.adapt_rate_spin.setRange(0.01, 0.5)
        self.adapt_rate_spin.setValue(0.05)
        self.adapt_rate_spin.setSingleStep(0.01)
        self.adapt_rate_spin.valueChanged.connect(self.params_changed.emit)
        adapt_layout.addWidget(self.adapt_rate_spin)
        gb_layout.addLayout(adapt_layout)

        layout.addWidget(gb_group)

        # Kazanç Ayarı
        gain_group = QGroupBox("Otomatik Kazanç Ayarı")
        gain_layout = QVBoxLayout(gain_group)

        self.auto_gain_check = QCheckBox("Otomatik Kazanç Aktif")
        self.auto_gain_check.setChecked(True)
        self.auto_gain_check.stateChanged.connect(self.params_changed.emit)
        gain_layout.addWidget(self.auto_gain_check)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Mod:"))
        self.gain_mode_combo = QComboBox()
        self.gain_mode_combo.addItems(["Üstel", "Doğrusal", "AGC", "Özel"])
        self.gain_mode_combo.currentIndexChanged.connect(self.params_changed.emit)
        mode_layout.addWidget(self.gain_mode_combo)
        gain_layout.addLayout(mode_layout)

        factor_layout = QHBoxLayout()
        factor_layout.addWidget(QLabel("Kazanç:"))
        self.gain_slider = QSlider(Qt.Orientation.Horizontal)
        self.gain_slider.setRange(10, 100)
        self.gain_slider.setValue(20)
        self.gain_slider.valueChanged.connect(self.params_changed.emit)
        factor_layout.addWidget(self.gain_slider)
        self.gain_value_label = QLabel("2.0")
        factor_layout.addWidget(self.gain_value_label)
        self.gain_slider.valueChanged.connect(
            lambda v: self.gain_value_label.setText(f"{v / 10:.1f}")
        )
        gain_layout.addLayout(factor_layout)

        agc_layout = QHBoxLayout()
        agc_layout.addWidget(QLabel("AGC Pencere:"))
        self.agc_window_spin = QSpinBox()
        self.agc_window_spin.setRange(10, 200)
        self.agc_window_spin.setValue(50)
        self.agc_window_spin.valueChanged.connect(self.params_changed.emit)
        agc_layout.addWidget(self.agc_window_spin)
        gain_layout.addLayout(agc_layout)

        self.auto_adjust_btn = QPushButton("Otomatik Ayarla")
        self.auto_adjust_btn.setStyleSheet("background-color: #FF5722; color: white;")
        gain_layout.addWidget(self.auto_adjust_btn)

        layout.addWidget(gain_group)

        # Filtre Ayarları
        filter_group = QGroupBox("Filtre Ayarları")
        filter_layout = QVBoxLayout(filter_group)

        self.bandpass_check = QCheckBox("Bant Geçiren Filtre")
        self.bandpass_check.setChecked(True)
        self.bandpass_check.stateChanged.connect(self.params_changed.emit)
        filter_layout.addWidget(self.bandpass_check)

        low_layout = QHBoxLayout()
        low_layout.addWidget(QLabel("Alt Frekans (MHz):"))
        self.low_freq_spin = QSpinBox()
        self.low_freq_spin.setRange(10, 500)
        self.low_freq_spin.setValue(100)
        self.low_freq_spin.valueChanged.connect(self.params_changed.emit)
        low_layout.addWidget(self.low_freq_spin)
        filter_layout.addLayout(low_layout)

        high_layout = QHBoxLayout()
        high_layout.addWidget(QLabel("Üst Frekans (MHz):"))
        self.high_freq_spin = QSpinBox()
        self.high_freq_spin.setRange(100, 2000)
        self.high_freq_spin.setValue(800)
        self.high_freq_spin.valueChanged.connect(self.params_changed.emit)
        high_layout.addWidget(self.high_freq_spin)
        filter_layout.addLayout(high_layout)

        self.hilbert_check = QCheckBox("Zarf Algılama (Hilbert)")
        self.hilbert_check.stateChanged.connect(self.params_changed.emit)
        filter_layout.addWidget(self.hilbert_check)

        self.dc_remove_check = QCheckBox("DC Ofset Kaldır")
        self.dc_remove_check.setChecked(True)
        self.dc_remove_check.stateChanged.connect(self.params_changed.emit)
        filter_layout.addWidget(self.dc_remove_check)

        layout.addWidget(filter_group)

    def get_gain_mode(self) -> str:
        """Seçili kazanç modunu döndürür."""
        modes = {
            0: "exponential",
            1: "linear",
            2: "agc",
            3: "custom",
        }
        return modes.get(self.gain_mode_combo.currentIndex(), "exponential")

    def get_gain_factor(self) -> float:
        """Kazanç faktörünü döndürür."""
        return self.gain_slider.value() / 10.0


class ScanSettingsPanel(QGroupBox):
    """Tarama ayarları paneli."""

    settings_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Tarama Ayarları", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Örnek sayısı
        samples_layout = QHBoxLayout()
        samples_layout.addWidget(QLabel("Örnek Sayısı:"))
        self.samples_combo = QComboBox()
        self.samples_combo.addItems(["256", "512", "1024", "2048"])
        self.samples_combo.setCurrentText("512")
        self.samples_combo.currentIndexChanged.connect(self.settings_changed.emit)
        samples_layout.addWidget(self.samples_combo)
        layout.addLayout(samples_layout)

        # Derinlik aralığı
        depth_layout = QHBoxLayout()
        depth_layout.addWidget(QLabel("Derinlik (m):"))
        self.depth_spin = QDoubleSpinBox()
        self.depth_spin.setRange(0.5, 30.0)
        self.depth_spin.setValue(5.0)
        self.depth_spin.setSingleStep(0.5)
        self.depth_spin.valueChanged.connect(self.settings_changed.emit)
        depth_layout.addWidget(self.depth_spin)
        layout.addLayout(depth_layout)

        # Anten frekansı
        freq_layout = QHBoxLayout()
        freq_layout.addWidget(QLabel("Anten (MHz):"))
        self.freq_combo = QComboBox()
        self.freq_combo.addItems(["100", "200", "300", "400", "500", "800", "1000"])
        self.freq_combo.setCurrentText("300")
        self.freq_combo.currentIndexChanged.connect(self.settings_changed.emit)
        freq_layout.addWidget(self.freq_combo)
        layout.addLayout(freq_layout)

        # İz aralığı
        spacing_layout = QHBoxLayout()
        spacing_layout.addWidget(QLabel("İz Aralığı (cm):"))
        self.spacing_spin = QDoubleSpinBox()
        self.spacing_spin.setRange(1.0, 50.0)
        self.spacing_spin.setValue(5.0)
        self.spacing_spin.setSingleStep(0.5)
        self.spacing_spin.valueChanged.connect(self.settings_changed.emit)
        spacing_layout.addWidget(self.spacing_spin)
        layout.addLayout(spacing_layout)

        # Renk haritası
        cmap_layout = QHBoxLayout()
        cmap_layout.addWidget(QLabel("Renk Haritası:"))
        self.colormap_combo = QComboBox()
        self.colormap_combo.addItems(
            ["viridis", "plasma", "inferno", "magma", "seismic", "jet", "gray"]
        )
        self.colormap_combo.currentIndexChanged.connect(self.settings_changed.emit)
        cmap_layout.addWidget(self.colormap_combo)
        layout.addLayout(cmap_layout)

        # Maks iz sayısı
        max_trace_layout = QHBoxLayout()
        max_trace_layout.addWidget(QLabel("Maks İz:"))
        self.max_trace_spin = QSpinBox()
        self.max_trace_spin.setRange(100, 5000)
        self.max_trace_spin.setValue(500)
        self.max_trace_spin.setSingleStep(100)
        self.max_trace_spin.valueChanged.connect(self.settings_changed.emit)
        max_trace_layout.addWidget(self.max_trace_spin)
        layout.addLayout(max_trace_layout)


class VisualizationPanel(QGroupBox):
    """3D görselleştirme kontrol paneli."""

    view_changed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__("3D Görselleştirme", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Görünüm seçimi
        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("Görünüm:"))
        self.view_combo = QComboBox()
        self.view_combo.addItems(["İzometrik", "Üst", "Ön", "Yan"])
        self.view_combo.currentIndexChanged.connect(self.view_changed.emit)
        view_layout.addWidget(self.view_combo)
        layout.addLayout(view_layout)

        # Saydamlık
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(QLabel("Saydamlık:"))
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(1, 100)
        self.opacity_slider.setValue(30)
        self.opacity_slider.valueChanged.connect(self.view_changed.emit)
        opacity_layout.addWidget(self.opacity_slider)
        layout.addLayout(opacity_layout)

        # Eşik değeri
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Eşik:"))
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(1, 100)
        self.threshold_slider.setValue(10)
        self.threshold_slider.valueChanged.connect(self.view_changed.emit)
        threshold_layout.addWidget(self.threshold_slider)
        layout.addLayout(threshold_layout)

        # Derinlik kesit
        depth_slice_layout = QHBoxLayout()
        depth_slice_layout.addWidget(QLabel("Derinlik Kesiti:"))
        self.depth_slice_slider = QSlider(Qt.Orientation.Horizontal)
        self.depth_slice_slider.setRange(0, 511)
        self.depth_slice_slider.setValue(100)
        self.depth_slice_slider.valueChanged.connect(self.view_changed.emit)
        depth_slice_layout.addWidget(self.depth_slice_slider)
        layout.addLayout(depth_slice_layout)

        # Kontrol butonları
        btn_layout = QHBoxLayout()
        self.update_3d_btn = QPushButton("3D Güncelle")
        self.update_3d_btn.setStyleSheet("background-color: #673AB7; color: white;")
        btn_layout.addWidget(self.update_3d_btn)

        self.clear_3d_btn = QPushButton("Temizle")
        btn_layout.addWidget(self.clear_3d_btn)
        layout.addLayout(btn_layout)

        # İzo-yüzey
        iso_layout = QHBoxLayout()
        self.iso_check = QCheckBox("İzo-yüzey")
        iso_layout.addWidget(self.iso_check)
        self.iso_value_spin = QDoubleSpinBox()
        self.iso_value_spin.setRange(0.1, 1.0)
        self.iso_value_spin.setValue(0.5)
        self.iso_value_spin.setSingleStep(0.1)
        iso_layout.addWidget(self.iso_value_spin)
        layout.addLayout(iso_layout)

        # C-scan kontrolü
        self.cscan_check = QCheckBox("C-Scan Kesiti Göster")
        layout.addWidget(self.cscan_check)

    def get_view_name(self) -> str:
        """Seçili görünüm adını döndürür."""
        views = {0: "iso", 1: "top", 2: "front", 3: "side"}
        return views.get(self.view_combo.currentIndex(), "iso")

    def get_opacity(self) -> float:
        return self.opacity_slider.value() / 100.0

    def get_threshold(self) -> float:
        return self.threshold_slider.value() / 100.0


class NotesPanel(QGroupBox):
    """Tarama notları paneli."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__("Tarama Notları", parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Tarama notlarınızı buraya yazın...")
        self.notes_edit.setMaximumHeight(100)
        layout.addWidget(self.notes_edit)

        # Konum bilgisi
        loc_layout = QHBoxLayout()
        loc_layout.addWidget(QLabel("Konum:"))
        self.location_edit = QTextEdit()
        self.location_edit.setPlaceholderText("Tarama konumu")
        self.location_edit.setMaximumHeight(30)
        loc_layout.addWidget(self.location_edit)
        layout.addLayout(loc_layout)

    def get_notes(self) -> str:
        return self.notes_edit.toPlainText()

    def get_location(self) -> str:
        return self.location_edit.toPlainText()

    def set_notes(self, text: str) -> None:
        self.notes_edit.setPlainText(text)

    def set_location(self, text: str) -> None:
        self.location_edit.setPlainText(text)
