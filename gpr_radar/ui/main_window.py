"""
GPR Radar Ana Pencere
Tork Pro 300 GPR uygulamasının ana kullanıcı arayüzü.
"""

import logging

import numpy as np
from PyQt5.QtCore import QTimer, pyqtSlot
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtWidgets import (
    QAction,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QScrollArea,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from gpr_radar.core.data_manager import DataManager, ScanMetadata, ScanSession
from gpr_radar.core.signal_processing import (
    AutoGainControl,
    GroundBalance,
    SignalProcessor,
)
from gpr_radar.device.tork_pro_300 import DeviceState, TorkPro300Device
from gpr_radar.ui.control_panel import (
    DevicePanel,
    NotesPanel,
    ProcessingPanel,
    ScanSettingsPanel,
    VisualizationPanel,
)
from gpr_radar.visualization.radar_plots import (
    AscanWidget,
    GainCurveWidget,
    RadargramWidget,
)
from gpr_radar.visualization.viewer_3d import Viewer3DWidget

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """GPR Radar uygulaması ana penceresi."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("GPR Radar - Tork Pro 300 | Farmet Teknoloji")
        self.setMinimumSize(1400, 900)

        # Bileşenleri oluştur
        self.device = TorkPro300Device()
        self.signal_processor = SignalProcessor()
        self.ground_balance = GroundBalance()
        self.auto_gain = AutoGainControl()
        self.data_manager = DataManager()
        self.current_session: ScanSession | None = None

        # İz sayacı
        self._trace_count = 0
        self._scan_lines_collected: list[np.ndarray] = []
        self._current_line_traces: list[np.ndarray] = []

        # Arayüzü oluştur
        self._setup_ui()
        self._setup_menus()
        self._setup_toolbar()
        self._setup_statusbar()
        self._connect_signals()

        # Güncelleme zamanlayıcısı
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(self._update_device_info)
        self._update_timer.start(1000)

        # Cihaz durumu geri çağırma
        self.device.set_on_status_change(self._on_device_state_changed)

        logger.info("Ana pencere oluşturuldu")

    def _setup_ui(self) -> None:
        """Ana arayüzü oluşturur."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # Sol panel - Kontroller (kaydırılabilir)
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setMaximumWidth(350)
        left_scroll.setMinimumWidth(280)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setSpacing(5)

        # Kontrol panelleri
        self.device_panel = DevicePanel()
        left_layout.addWidget(self.device_panel)

        self.processing_panel = ProcessingPanel()
        left_layout.addWidget(self.processing_panel)

        self.scan_settings_panel = ScanSettingsPanel()
        left_layout.addWidget(self.scan_settings_panel)

        self.viz_panel = VisualizationPanel()
        left_layout.addWidget(self.viz_panel)

        self.notes_panel = NotesPanel()
        left_layout.addWidget(self.notes_panel)

        left_layout.addStretch()
        left_scroll.setWidget(left_panel)

        # Sağ panel - Görselleştirmeler
        right_splitter = QSplitter()
        right_splitter.setOrientation(2)  # Vertical

        # Üst: Radargram ve A-scan
        top_widget = QWidget()
        top_layout = QHBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Radargram (B-scan)
        self.radargram_widget = RadargramWidget()
        top_layout.addWidget(self.radargram_widget, stretch=3)

        # A-scan ve kazanç eğrisi
        right_plots = QTabWidget()
        self.ascan_widget = AscanWidget()
        right_plots.addTab(self.ascan_widget, "A-Scan")
        self.gain_curve_widget = GainCurveWidget()
        right_plots.addTab(self.gain_curve_widget, "Kazanç Eğrisi")
        top_layout.addWidget(right_plots, stretch=1)

        right_splitter.addWidget(top_widget)

        # Alt: 3D Görselleştirme
        self.viewer_3d = Viewer3DWidget()
        right_splitter.addWidget(self.viewer_3d)

        # Oranları ayarla
        right_splitter.setSizes([500, 400])

        # Ana düzen
        main_layout.addWidget(left_scroll)
        main_layout.addWidget(right_splitter, stretch=1)

    def _setup_menus(self) -> None:
        """Menü çubuğunu oluşturur."""
        menubar = self.menuBar()
        assert isinstance(menubar, QMenuBar)

        # Dosya menüsü
        file_menu = menubar.addMenu("Dosya")

        new_action = QAction("Yeni Tarama", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_session)
        file_menu.addAction(new_action)

        open_action = QAction("Tarama Aç...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_session)
        file_menu.addAction(open_action)

        save_action = QAction("Taramayı Kaydet", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_session)
        file_menu.addAction(save_action)

        file_menu.addSeparator()

        export_menu = file_menu.addMenu("Dışa Aktar")

        export_csv = QAction("CSV olarak...", self)
        export_csv.triggered.connect(lambda: self._export_data("csv"))
        export_menu.addAction(export_csv)

        export_numpy = QAction("NumPy olarak...", self)
        export_numpy.triggered.connect(lambda: self._export_data("numpy"))
        export_menu.addAction(export_numpy)

        export_image = QAction("Görüntü olarak...", self)
        export_image.triggered.connect(lambda: self._export_data("image"))
        export_menu.addAction(export_image)

        file_menu.addSeparator()

        quit_action = QAction("Çıkış", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # İşleme menüsü
        process_menu = menubar.addMenu("İşleme")

        auto_all = QAction("Tümünü Otomatik İşle", self)
        auto_all.triggered.connect(self._process_all)
        process_menu.addAction(auto_all)

        migration_action = QAction("Migrasyon Uygula", self)
        migration_action.triggered.connect(self._apply_migration)
        process_menu.addAction(migration_action)

        process_menu.addSeparator()

        reset_proc = QAction("İşlemeyi Sıfırla", self)
        reset_proc.triggered.connect(self._reset_processing)
        process_menu.addAction(reset_proc)

        # Görünüm menüsü
        view_menu = menubar.addMenu("Görünüm")

        for cmap in ["viridis", "plasma", "seismic", "jet", "gray"]:
            action = QAction(f"Renk: {cmap}", self)
            action.triggered.connect(
                lambda checked, c=cmap: self.radargram_widget.set_colormap(c)
            )
            view_menu.addAction(action)

        # Yardım menüsü
        help_menu = menubar.addMenu("Yardım")

        about_action = QAction("Hakkında", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_toolbar(self) -> None:
        """Araç çubuğunu oluşturur."""
        toolbar = QToolBar("Ana Araç Çubuğu")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Yeni tarama
        new_btn = QAction("Yeni", self)
        new_btn.triggered.connect(self._new_session)
        toolbar.addAction(new_btn)

        # Aç
        open_btn = QAction("Aç", self)
        open_btn.triggered.connect(self._open_session)
        toolbar.addAction(open_btn)

        # Kaydet
        save_btn = QAction("Kaydet", self)
        save_btn.triggered.connect(self._save_session)
        toolbar.addAction(save_btn)

        toolbar.addSeparator()

        # İşleme
        process_btn = QAction("Otomatik İşle", self)
        process_btn.triggered.connect(self._process_all)
        toolbar.addAction(process_btn)

        # Migrasyon
        migrate_btn = QAction("Migrasyon", self)
        migrate_btn.triggered.connect(self._apply_migration)
        toolbar.addAction(migrate_btn)

        toolbar.addSeparator()

        # 3D güncelle
        update_3d_btn = QAction("3D Güncelle", self)
        update_3d_btn.triggered.connect(self._update_3d_view)
        toolbar.addAction(update_3d_btn)

    def _setup_statusbar(self) -> None:
        """Durum çubuğunu oluşturur."""
        statusbar = self.statusBar()
        assert isinstance(statusbar, QStatusBar)

        self.status_label = QLabel("Hazır")
        statusbar.addWidget(self.status_label, stretch=1)

        self.trace_count_label = QLabel("İz: 0")
        statusbar.addPermanentWidget(self.trace_count_label)

        self.connection_label = QLabel("Bağlı Değil")
        self.connection_label.setStyleSheet(
            "color: red; font-weight: bold; padding: 2px 8px;"
        )
        statusbar.addPermanentWidget(self.connection_label)

    def _connect_signals(self) -> None:
        """Sinyal bağlantılarını kurar."""
        # Cihaz paneli sinyalleri
        self.device_panel.connect_clicked.connect(self._connect_device)
        self.device_panel.disconnect_clicked.connect(self._disconnect_device)
        self.device_panel.scan_start_clicked.connect(self._start_scan)
        self.device_panel.scan_stop_clicked.connect(self._stop_scan)
        self.device_panel.simulate_clicked.connect(self._start_simulation)
        self.device_panel.refresh_btn.clicked.connect(self._refresh_ports)

        # İşleme paneli sinyalleri
        self.processing_panel.params_changed.connect(self._on_params_changed)
        self.processing_panel.calibrate_btn.clicked.connect(self._calibrate_ground)
        self.processing_panel.auto_adjust_btn.clicked.connect(self._auto_adjust_gain)

        # Tarama ayarları
        self.scan_settings_panel.settings_changed.connect(self._on_settings_changed)

        # 3D görselleştirme
        self.viz_panel.update_3d_btn.clicked.connect(self._update_3d_view)
        self.viz_panel.clear_3d_btn.clicked.connect(self.viewer_3d.clear)
        self.viz_panel.view_changed.connect(self._on_view_changed)

        # Radargram imleci
        self.radargram_widget.cursor_moved.connect(self._on_cursor_moved)

    # === Cihaz İşlemleri ===

    @pyqtSlot(str, int)
    def _connect_device(self, port: str, baud_rate: int) -> None:
        """Cihaza bağlanır."""
        # Port adından port bilgisini ayıkla
        actual_port = port.split(" - ")[0] if " - " in port else port
        success = self.device.connect(actual_port, baud_rate)
        if success:
            self._new_session()
            self.status_label.setText("Cihaz bağlandı")
        else:
            QMessageBox.critical(self, "Hata", "Cihaza bağlanılamadı!")

    @pyqtSlot()
    def _start_simulation(self) -> None:
        """Simülasyon modunu başlatır."""
        success = self.device.connect()  # Boş port = simülasyon
        if success:
            self._new_session()
            self.status_label.setText("Simülasyon modu aktif")

    @pyqtSlot()
    def _disconnect_device(self) -> None:
        """Cihaz bağlantısını keser."""
        self.device.disconnect()
        self.status_label.setText("Cihaz bağlantısı kesildi")

    @pyqtSlot()
    def _start_scan(self) -> None:
        """Taramayı başlatır."""
        if self.current_session is None:
            self._new_session()

        self._apply_scan_settings()
        success = self.device.start_scan(callback=self._on_new_trace)
        if success:
            self.status_label.setText("Tarama yapılıyor...")
        else:
            QMessageBox.warning(self, "Uyarı", "Tarama başlatılamadı!")

    @pyqtSlot()
    def _stop_scan(self) -> None:
        """Taramayı durdurur."""
        self.device.stop_scan()
        self.status_label.setText("Tarama durduruldu")

        # Mevcut çizgiyi 3D taramaya ekle
        if len(self._current_line_traces) > 0:
            line_data = np.column_stack(self._current_line_traces)
            self._scan_lines_collected.append(line_data)
            if self.current_session:
                self.current_session.add_scan_line(line_data)
            self._current_line_traces = []

    @pyqtSlot()
    def _refresh_ports(self) -> None:
        """Kullanılabilir portları yeniler."""
        ports = TorkPro300Device.list_available_ports()
        self.device_panel.update_ports(ports)

    def _apply_scan_settings(self) -> None:
        """Tarama ayarlarını cihaza uygular."""
        num_samples = int(self.scan_settings_panel.samples_combo.currentText())
        depth = self.scan_settings_panel.depth_spin.value()
        freq = float(self.scan_settings_panel.freq_combo.currentText()) * 1e6

        self.device.set_scan_parameters(
            num_samples=num_samples,
            scan_depth=depth,
            antenna_freq=freq,
        )

        self.signal_processor.num_samples = num_samples
        self.auto_gain.num_samples = num_samples
        self.radargram_widget.set_max_traces(
            self.scan_settings_panel.max_trace_spin.value()
        )

    # === Veri İşleme ===

    def _on_new_trace(self, raw_trace: np.ndarray) -> None:
        """
        Yeni iz alındığında çağrılır (cihaz thread'inden).

        Args:
            raw_trace: Ham iz verisi
        """
        self._trace_count += 1
        trace = raw_trace.copy()

        # Oturuma ekle
        if self.current_session:
            self.current_session.add_trace(raw_trace)

        # Mevcut çizgi izlerini topla
        self._current_line_traces.append(raw_trace.copy())

        # Sinyal işleme uygula
        processed_trace = self._process_trace(trace)

        # GUI'yi güncelle (thread-safe olmayabilir, QTimer ile güncelle)
        QTimer.singleShot(0, lambda: self._update_display(processed_trace, raw_trace))

    def _process_trace(self, trace: np.ndarray) -> np.ndarray:
        """
        Tek iz için sinyal işleme zinciri uygular.

        Args:
            trace: Ham iz verisi

        Returns:
            İşlenmiş iz verisi
        """
        result = trace.copy()

        # DC ofset kaldır
        if self.processing_panel.dc_remove_check.isChecked():
            result = self.signal_processor.remove_dc_offset(result)

        # Toprak ayarı
        if self.processing_panel.ground_balance_check.isChecked():
            result = self.ground_balance.apply(result)
            self.ground_balance.adaptive_update(trace)

        # Bant geçiren filtre
        if self.processing_panel.bandpass_check.isChecked():
            low_freq = self.processing_panel.low_freq_spin.value() * 1e6
            high_freq = self.processing_panel.high_freq_spin.value() * 1e6
            result = self.signal_processor.bandpass_filter(result, low_freq, high_freq)

        # Kazanç uygula
        if self.processing_panel.auto_gain_check.isChecked():
            self.auto_gain.gain_mode = self.processing_panel.get_gain_mode()
            self.auto_gain.gain_factor = self.processing_panel.get_gain_factor()
            self.auto_gain.agc_window = self.processing_panel.agc_window_spin.value()
            result = self.auto_gain.apply(result)

        # Hilbert dönüşümü
        if self.processing_panel.hilbert_check.isChecked():
            result = self.signal_processor.hilbert_transform(result)

        return result

    def _update_display(
        self, processed_trace: np.ndarray, raw_trace: np.ndarray
    ) -> None:
        """Görsel öğeleri günceller."""
        # Radargram güncelle
        self.radargram_widget.append_trace(processed_trace)

        # A-scan güncelle
        envelope = self.signal_processor.hilbert_transform(processed_trace)
        self.ascan_widget.update_trace(processed_trace, envelope)

        # Kazanç eğrisi güncelle
        gain_curve = self.auto_gain.get_current_curve()
        self.gain_curve_widget.update_curve(gain_curve)

        # İz sayacı güncelle
        self.trace_count_label.setText(f"İz: {self._trace_count}")

    @pyqtSlot()
    def _process_all(self) -> None:
        """Tüm verileri toplu işler."""
        if self.current_session is None:
            return

        radargram = self.current_session.get_radargram()
        if radargram.size == 0:
            QMessageBox.information(self, "Bilgi", "İşlenecek veri yok.")
            return

        self.status_label.setText("Veri işleniyor...")

        processed = radargram.copy()

        # DC ofset kaldır
        if self.processing_panel.dc_remove_check.isChecked():
            for i in range(processed.shape[1]):
                processed[:, i] = self.signal_processor.remove_dc_offset(
                    processed[:, i]
                )

        # Toprak ayarı
        if self.processing_panel.ground_balance_check.isChecked():
            processed = self.ground_balance.apply(processed)

        # Bant geçiren filtre
        if self.processing_panel.bandpass_check.isChecked():
            low_freq = self.processing_panel.low_freq_spin.value() * 1e6
            high_freq = self.processing_panel.high_freq_spin.value() * 1e6
            processed = self.signal_processor.bandpass_filter(
                processed, low_freq, high_freq
            )

        # Kazanç uygula
        if self.processing_panel.auto_gain_check.isChecked():
            self.auto_gain.gain_mode = self.processing_panel.get_gain_mode()
            self.auto_gain.gain_factor = self.processing_panel.get_gain_factor()
            processed = self.auto_gain.apply(processed)

        # Hilbert dönüşümü
        if self.processing_panel.hilbert_check.isChecked():
            processed = self.signal_processor.hilbert_transform(processed)

        self.current_session.processed_data = processed
        self.radargram_widget.update_data(processed)
        self.status_label.setText("İşleme tamamlandı")

    @pyqtSlot()
    def _apply_migration(self) -> None:
        """Migrasyon uygular."""
        if self.current_session is None:
            return

        data = self.current_session.processed_data
        if data is None:
            data = self.current_session.get_radargram()
        if data.size == 0:
            return

        self.status_label.setText("Migrasyon uygulanıyor (bu biraz sürebilir)...")
        migrated = self.signal_processor.migration_kirchhoff(data)
        self.current_session.processed_data = migrated
        self.radargram_widget.update_data(migrated)
        self.status_label.setText("Migrasyon tamamlandı")

    @pyqtSlot()
    def _reset_processing(self) -> None:
        """İşlemeyi sıfırlar, ham veriyi gösterir."""
        if self.current_session is None:
            return

        radargram = self.current_session.get_radargram()
        if radargram.size > 0:
            self.current_session.processed_data = None
            self.radargram_widget.update_data(radargram)
            self.status_label.setText("İşleme sıfırlandı")

    # === Toprak ve Kazanç Ayarları ===

    @pyqtSlot()
    def _calibrate_ground(self) -> None:
        """Toprak kalibrasyonu yapar."""
        if self.current_session is None:
            QMessageBox.warning(
                self, "Uyarı", "Kalibrasyon için önce tarama başlatın."
            )
            return

        radargram = self.current_session.get_radargram()
        if radargram.size == 0:
            QMessageBox.warning(
                self, "Uyarı", "Kalibrasyon için yeterli veri yok."
            )
            return

        # Son izleri kalibrasyon için kullan
        num_cal_traces = min(20, radargram.shape[1])
        cal_data = radargram[:, -num_cal_traces:]

        self.ground_balance.reset()
        self.ground_balance.calibrate(cal_data)

        if self.ground_balance.is_calibrated:
            QMessageBox.information(
                self,
                "Kalibrasyon",
                f"Toprak kalibrasyonu tamamlandı.\n{num_cal_traces} iz kullanıldı.",
            )
            self.status_label.setText("Toprak kalibrasyonu tamamlandı")
        else:
            QMessageBox.warning(
                self, "Uyarı", "Kalibrasyon başarısız. Daha fazla veri gerekli."
            )

    @pyqtSlot()
    def _auto_adjust_gain(self) -> None:
        """Kazancı otomatik ayarlar."""
        if self.current_session is None:
            return

        radargram = self.current_session.get_radargram()
        if radargram.size == 0:
            return

        self.auto_gain.auto_adjust(radargram)
        gain_value = self.auto_gain.gain_factor

        # Slider'ı güncelle
        self.processing_panel.gain_slider.setValue(int(gain_value * 10))
        self.status_label.setText(f"Kazanç otomatik ayarlandı: {gain_value:.1f}")

    # === 3D Görselleştirme ===

    @pyqtSlot()
    def _update_3d_view(self) -> None:
        """3D görünümü günceller."""
        if self.current_session is None:
            return

        # 3D hacim verisi oluştur
        volume = self.current_session.get_3d_volume()

        if volume is None:
            # 2D veriden sözde-3D oluştur
            radargram = self.current_session.get_radargram()
            if radargram.size == 0:
                return

            # Radargram'ı birkaç katmana böl
            n_layers = min(10, radargram.shape[1] // 5)
            if n_layers < 2:
                n_layers = 2

            traces_per_layer = radargram.shape[1] // n_layers
            layers = []
            for i in range(n_layers):
                start = i * traces_per_layer
                end = start + traces_per_layer
                layers.append(radargram[:, start:end])

            volume = np.stack(layers, axis=2)

        opacity = self.viz_panel.get_opacity()
        threshold = self.viz_panel.get_threshold()
        colormap = self.scan_settings_panel.colormap_combo.currentText()

        self.viewer_3d.update_volume(volume, opacity, threshold, colormap)

        # C-scan kesiti
        if self.viz_panel.cscan_check.isChecked():
            depth_idx = self.viz_panel.depth_slice_slider.value()
            self.viewer_3d.add_depth_slice(volume, depth_idx, colormap)

        # İzo-yüzey
        if self.viz_panel.iso_check.isChecked():
            iso_val = self.viz_panel.iso_value_spin.value()
            self.viewer_3d.add_isosurface(volume, iso_val)

        # Görünümü ayarla
        view_name = self.viz_panel.get_view_name()
        self.viewer_3d.set_view(view_name)

        self.status_label.setText("3D görünüm güncellendi")

    @pyqtSlot()
    def _on_view_changed(self) -> None:
        """Görünüm parametreleri değiştiğinde."""
        view_name = self.viz_panel.get_view_name()
        self.viewer_3d.set_view(view_name)

    # === Oturum Yönetimi ===

    @pyqtSlot()
    def _new_session(self) -> None:
        """Yeni tarama oturumu oluşturur."""
        metadata = ScanMetadata(
            device="Tork Pro 300",
            sample_rate=self.device.sample_rate,
            num_samples=self.device.num_samples,
            depth_range=self.device.scan_depth,
            antenna_freq=self.device.antenna_freq,
        )
        self.current_session = ScanSession(metadata=metadata)
        self._trace_count = 0
        self._scan_lines_collected = []
        self._current_line_traces = []

        # Görüntüleri temizle
        self.radargram_widget.clear_data()
        self.ascan_widget.clear_data()
        self.gain_curve_widget.clear_data()
        self.viewer_3d.clear()
        self.ground_balance.reset()

        self.trace_count_label.setText("İz: 0")
        self.status_label.setText("Yeni tarama oturumu oluşturuldu")

    @pyqtSlot()
    def _save_session(self) -> None:
        """Tarama oturumunu kaydeder."""
        if self.current_session is None:
            QMessageBox.warning(self, "Uyarı", "Kaydedilecek tarama yok.")
            return

        # Notları ekle
        self.current_session.metadata.notes = self.notes_panel.get_notes()
        self.current_session.metadata.location = self.notes_panel.get_location()

        filepath = self.data_manager.save_session(self.current_session)
        self.status_label.setText(f"Tarama kaydedildi: {filepath}")
        QMessageBox.information(
            self, "Kayıt", f"Tarama başarıyla kaydedildi:\n{filepath}"
        )

    @pyqtSlot()
    def _open_session(self) -> None:
        """Kayıtlı tarama oturumunu açar."""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Tarama Dosyası Aç", self.data_manager.data_dir, "HDF5 (*.h5)"
        )

        if filepath:
            try:
                self.current_session = self.data_manager.load_session(filepath)
                radargram = self.current_session.get_radargram()
                if radargram.size > 0:
                    self.radargram_widget.update_data(radargram)
                    self._trace_count = radargram.shape[1]
                    self.trace_count_label.setText(f"İz: {self._trace_count}")

                # Notları yükle
                self.notes_panel.set_notes(self.current_session.metadata.notes)
                self.notes_panel.set_location(self.current_session.metadata.location)

                self.status_label.setText(f"Tarama yüklendi: {filepath}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Hata", f"Dosya açılamadı:\n{e}"
                )

    def _export_data(self, export_format: str) -> None:
        """Veriyi dışa aktarır."""
        if self.current_session is None:
            QMessageBox.warning(self, "Uyarı", "Dışa aktarılacak veri yok.")
            return

        filters = {
            "csv": ("CSV Dosyası (*.csv)", ".csv"),
            "numpy": ("NumPy Dosyası (*.npy)", ".npy"),
            "image": ("PNG Görüntü (*.png)", ".png"),
        }

        filter_str, ext = filters.get(export_format, ("", ""))
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Dışa Aktar", f"gpr_export{ext}", filter_str
        )

        if filepath:
            try:
                if export_format == "csv":
                    self.data_manager.export_csv(self.current_session, filepath)
                elif export_format == "numpy":
                    self.data_manager.export_numpy(self.current_session, filepath)
                elif export_format == "image":
                    self.data_manager.export_image(self.current_session, filepath)

                self.status_label.setText(f"Dışa aktarıldı: {filepath}")
            except Exception as e:
                QMessageBox.critical(
                    self, "Hata", f"Dışa aktarma hatası:\n{e}"
                )

    # === Geri Çağırmalar ===

    def _on_device_state_changed(self, state: DeviceState) -> None:
        """Cihaz durumu değiştiğinde."""
        QTimer.singleShot(0, lambda: self._update_ui_state(state))

    def _update_ui_state(self, state: DeviceState) -> None:
        """Arayüzü cihaz durumuna göre günceller."""
        is_connected = state in (DeviceState.CONNECTED, DeviceState.SCANNING)
        is_scanning = state == DeviceState.SCANNING

        self.device_panel.set_connected(is_connected)
        self.device_panel.set_scanning(is_scanning)
        self.device_panel.update_status(state.value)

        # Durum çubuğu rengi
        color_map = {
            DeviceState.DISCONNECTED: ("red", "Bağlı Değil"),
            DeviceState.CONNECTING: ("orange", "Bağlanıyor..."),
            DeviceState.CONNECTED: ("green", "Bağlı"),
            DeviceState.SCANNING: ("blue", "Tarama Yapılıyor"),
            DeviceState.ERROR: ("red", "HATA"),
            DeviceState.CALIBRATING: ("purple", "Kalibrasyon"),
        }
        color, text = color_map.get(state, ("gray", "Bilinmiyor"))
        self.connection_label.setText(text)
        self.connection_label.setStyleSheet(
            f"color: {color}; font-weight: bold; padding: 2px 8px;"
        )

    @pyqtSlot()
    def _update_device_info(self) -> None:
        """Cihaz bilgilerini periyodik olarak günceller."""
        if self.device.is_connected:
            self.device_panel.update_device_info(
                self.device.battery_level, self.device.temperature
            )

    @pyqtSlot()
    def _on_params_changed(self) -> None:
        """İşleme parametreleri değiştiğinde."""
        # Adaptasyon hızını güncelle
        self.ground_balance.adaptation_rate = (
            self.processing_panel.adapt_rate_spin.value()
        )

    @pyqtSlot()
    def _on_settings_changed(self) -> None:
        """Tarama ayarları değiştiğinde."""
        colormap = self.scan_settings_panel.colormap_combo.currentText()
        self.radargram_widget.set_colormap(colormap)
        self.radargram_widget.set_max_traces(
            self.scan_settings_panel.max_trace_spin.value()
        )

    @pyqtSlot(int, int)
    def _on_cursor_moved(self, trace_idx: int, sample_idx: int) -> None:
        """Radargram imleci hareket ettiğinde A-scan günceller."""
        if self.current_session is None:
            return

        radargram = self.current_session.get_radargram()
        if radargram.size == 0:
            return

        if 0 <= trace_idx < radargram.shape[1]:
            trace = radargram[:, trace_idx]
            processed = self._process_trace(trace)
            envelope = self.signal_processor.hilbert_transform(processed)
            self.ascan_widget.update_trace(processed, envelope)

    def _show_about(self) -> None:
        """Hakkında penceresini gösterir."""
        QMessageBox.about(
            self,
            "Hakkında",
            "<h2>GPR Radar - Tork Pro 300</h2>"
            "<p>Farmet Teknoloji GPR Analiz Yazılımı</p>"
            "<p><b>Sürüm:</b> 1.0.0</p>"
            "<p><b>Özellikler:</b></p>"
            "<ul>"
            "<li>Gerçek Zamanlı 3D Analiz</li>"
            "<li>Otomatik Toprak Ayarı</li>"
            "<li>Otomatik Kazanç Kontrolü</li>"
            "<li>Tork Pro 300 Entegrasyonu</li>"
            "</ul>"
            "<p>Farmet Teknoloji &copy; 2024</p>",
        )

    def closeEvent(self, event: QCloseEvent) -> None:
        """Pencere kapanırken cihaz bağlantısını keser."""
        if self.device.is_scanning:
            self.device.stop_scan()
        if self.device.is_connected:
            self.device.disconnect()
        event.accept()
