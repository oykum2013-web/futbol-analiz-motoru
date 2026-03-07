"""
GPR Radar 2D Görselleştirme Modülü
B-scan, A-scan ve radargram görüntüleme.
"""

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QVBoxLayout, QWidget


class RadargramWidget(QWidget):
    """B-scan (radargram) görselleştirme widget'ı."""

    cursor_moved = pyqtSignal(int, int)  # trace_idx, sample_idx

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()
        self._data: np.ndarray | None = None
        self._colormap = "viridis"
        self._max_traces = 500

    def _setup_ui(self) -> None:
        """Arayüzü oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Radargram görüntü widget'ı
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Derinlik (örnek)")
        self.plot_widget.setLabel("bottom", "İz Numarası")
        self.plot_widget.setTitle("B-Scan Radargram")

        self.image_item = pg.ImageItem()
        self.plot_widget.addItem(self.image_item)

        # Renk haritası
        colormap = pg.colormap.get("viridis")
        self.color_bar = pg.ColorBarItem(
            colorMap=colormap, interactive=False, width=15
        )
        self.color_bar.setImageItem(self.image_item)

        # İmleç çizgileri
        self.v_line = pg.InfiniteLine(angle=90, movable=True, pen="y")
        self.h_line = pg.InfiniteLine(angle=0, movable=True, pen="y")
        self.plot_widget.addItem(self.v_line, ignoreBounds=True)
        self.plot_widget.addItem(self.h_line, ignoreBounds=True)

        self.v_line.sigPositionChanged.connect(self._on_cursor_moved)
        self.h_line.sigPositionChanged.connect(self._on_cursor_moved)

        layout.addWidget(self.plot_widget)

    def update_data(self, data: np.ndarray) -> None:
        """
        Radargram verisini günceller.

        Args:
            data: 2D radargram verisi (samples x traces)
        """
        if data.size == 0:
            return

        self._data = data

        # Görüntüyü güncelle (transpose: pyqtgraph x=sütun, y=satır bekler)
        display_data = data.T
        self.image_item.setImage(display_data, autoLevels=True)

    def append_trace(self, trace: np.ndarray) -> None:
        """
        Yeni iz ekler ve görüntüyü günceller.

        Args:
            trace: Yeni iz verisi
        """
        if self._data is None:
            self._data = trace.reshape(-1, 1)
        else:
            self._data = np.column_stack([self._data, trace])
            # Maksimum iz sayısını sınırla
            if self._data.shape[1] > self._max_traces:
                self._data = self._data[:, -self._max_traces :]

        self.update_data(self._data)

    def set_colormap(self, name: str) -> None:
        """Renk haritasını değiştirir."""
        try:
            colormap = pg.colormap.get(name)
            self.color_bar.setColorMap(colormap)
            lut = colormap.getLookupTable(nPts=256)
            self.image_item.setLookupTable(lut)
            self._colormap = name
        except Exception:
            pass

    def clear_data(self) -> None:
        """Verileri temizler."""
        self._data = None
        self.image_item.clear()

    def set_max_traces(self, max_traces: int) -> None:
        """Maksimum iz sayısını ayarlar."""
        self._max_traces = max_traces

    def _on_cursor_moved(self) -> None:
        """İmleç hareket ettiğinde çağrılır."""
        trace_idx = int(self.v_line.value())
        sample_idx = int(self.h_line.value())
        self.cursor_moved.emit(trace_idx, sample_idx)


class AscanWidget(QWidget):
    """A-scan (tek iz) görselleştirme widget'ı."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Arayüzü oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Genlik")
        self.plot_widget.setLabel("bottom", "Derinlik (örnek)")
        self.plot_widget.setTitle("A-Scan")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.trace_curve = self.plot_widget.plot(pen=pg.mkPen("g", width=1))
        self.envelope_curve = self.plot_widget.plot(
            pen=pg.mkPen("r", width=1, style=Qt.PenStyle.DashLine)
        )

        layout.addWidget(self.plot_widget)

    def update_trace(
        self, trace: np.ndarray, envelope: np.ndarray | None = None
    ) -> None:
        """
        İz verisini günceller.

        Args:
            trace: İz verisi
            envelope: Zarf verisi (opsiyonel)
        """
        x = np.arange(len(trace))
        self.trace_curve.setData(x, trace)

        if envelope is not None:
            self.envelope_curve.setData(x, envelope)
        else:
            self.envelope_curve.clear()

    def clear_data(self) -> None:
        """Verileri temizler."""
        self.trace_curve.clear()
        self.envelope_curve.clear()


class GainCurveWidget(QWidget):
    """Kazanç eğrisi görselleştirme widget'ı."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Arayüzü oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel("left", "Kazanç")
        self.plot_widget.setLabel("bottom", "Derinlik (örnek)")
        self.plot_widget.setTitle("Kazanç Eğrisi")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)

        self.gain_curve = self.plot_widget.plot(pen=pg.mkPen("c", width=2))

        layout.addWidget(self.plot_widget)

    def update_curve(self, curve: np.ndarray) -> None:
        """Kazanç eğrisini günceller."""
        x = np.arange(len(curve))
        self.gain_curve.setData(x, curve)

    def clear_data(self) -> None:
        """Verileri temizler."""
        self.gain_curve.clear()
