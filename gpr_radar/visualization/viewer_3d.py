"""
GPR Radar 3D Görselleştirme Modülü
3D hacimsel veri görselleştirme ve analiz.
"""

import numpy as np
from PyQt5.QtWidgets import QVBoxLayout, QWidget

try:
    import pyvista as pv
    from pyvistaqt import QtInteractor

    PYVISTA_AVAILABLE = True
except ImportError:
    PYVISTA_AVAILABLE = False


class Viewer3DWidget(QWidget):
    """3D GPR veri görselleştirme widget'ı."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._volume_data: np.ndarray | None = None
        self._plotter: "QtInteractor | None" = None
        self._use_pyvista = PYVISTA_AVAILABLE
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Arayüzü oluşturur."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        if self._use_pyvista:
            try:
                self._plotter = QtInteractor(self)
                self._plotter.set_background("black")
                self._plotter.add_axes()
                layout.addWidget(self._plotter.interactor)
            except Exception:
                self._use_pyvista = False
                self._setup_fallback(layout)
        else:
            self._setup_fallback(layout)

    def _setup_fallback(self, layout: QVBoxLayout) -> None:
        """PyVista kullanılamadığında yedek görselleştirme."""
        import pyqtgraph.opengl as gl

        self._gl_widget = gl.GLViewWidget()
        self._gl_widget.setCameraPosition(distance=40)
        self._gl_widget.setBackgroundColor("k")

        # Izgara ekle
        grid = gl.GLGridItem()
        grid.setSize(20, 20, 1)
        grid.setSpacing(1, 1, 1)
        self._gl_widget.addItem(grid)

        layout.addWidget(self._gl_widget)

    def update_volume(
        self,
        data: np.ndarray,
        opacity: float = 0.3,
        threshold: float = 0.1,
        colormap: str = "jet",
    ) -> None:
        """
        3D hacimsel veriyi günceller ve görselleştirir.

        Args:
            data: 3D veri dizisi (samples x traces x lines)
            opacity: Saydamlık (0-1)
            threshold: Eşik değeri (bu değerin altındaki veriler gizlenir)
            colormap: Renk haritası adı
        """
        self._volume_data = data

        if self._use_pyvista and self._plotter is not None:
            self._render_pyvista(data, opacity, threshold, colormap)
        else:
            self._render_opengl(data, opacity, threshold)

    def _render_pyvista(
        self,
        data: np.ndarray,
        opacity: float,
        threshold: float,
        colormap: str,
    ) -> None:
        """PyVista ile 3D görselleştirme."""
        if self._plotter is None:
            return

        self._plotter.clear()

        # Veriyi normalize et
        norm_data = data.copy()
        max_val = np.max(np.abs(norm_data))
        if max_val > 0:
            norm_data = norm_data / max_val

        # PyVista UniformGrid oluştur
        grid = pv.ImageData(
            dimensions=(data.shape[0], data.shape[1], data.shape[2]),
            spacing=(1.0, 1.0, 1.0),
            origin=(0.0, 0.0, 0.0),
        )
        grid.point_data["amplitude"] = norm_data.flatten(order="F")

        # Eşik üstü veriyi göster
        thresholded = grid.threshold(threshold, scalars="amplitude")
        if thresholded.n_points > 0:
            self._plotter.add_mesh(
                thresholded,
                scalars="amplitude",
                cmap=colormap,
                opacity=opacity,
                show_scalar_bar=True,
                scalar_bar_args={"title": "Genlik", "vertical": True},
            )

        # Eksen etiketleri
        self._plotter.add_axes(
            xlabel="İz",
            ylabel="Derinlik",
            zlabel="Çizgi",
        )

        self._plotter.reset_camera()
        self._plotter.render()

    def _render_opengl(
        self, data: np.ndarray, opacity: float, threshold: float
    ) -> None:
        """OpenGL ile yedek 3D görselleştirme."""
        import pyqtgraph.opengl as gl

        if not hasattr(self, "_gl_widget"):
            return

        # Önceki mesh'leri temizle (ızgara hariç)
        items_to_remove = []
        for item in self._gl_widget.items:
            if not isinstance(item, gl.GLGridItem):
                items_to_remove.append(item)
        for item in items_to_remove:
            self._gl_widget.removeItem(item)

        # Veriyi normalize et
        norm_data = np.abs(data.copy())
        max_val = np.max(norm_data)
        if max_val > 0:
            norm_data = norm_data / max_val

        # Eşik uygula
        mask = norm_data > threshold

        if not np.any(mask):
            return

        # Nokta bulutu olarak göster
        points = np.array(np.where(mask)).T.astype(np.float32)
        values = norm_data[mask]

        # Renk haritası oluştur
        colors = np.zeros((len(values), 4), dtype=np.float32)
        colors[:, 0] = values  # Kırmızı
        colors[:, 1] = 0.2  # Yeşil
        colors[:, 2] = 1.0 - values  # Mavi
        colors[:, 3] = opacity  # Alfa

        # Ölçeklendirme
        scale_factor = 20.0 / max(data.shape)
        points *= scale_factor

        scatter = gl.GLScatterPlotItem(
            pos=points,
            color=colors,
            size=3,
            pxMode=True,
        )
        self._gl_widget.addItem(scatter)

    def add_depth_slice(
        self, data: np.ndarray, depth_idx: int, colormap: str = "jet"
    ) -> None:
        """
        Belirli derinlikte C-scan (yatay kesit) ekler.

        Args:
            data: 3D veri dizisi
            depth_idx: Derinlik indeksi
            colormap: Renk haritası
        """
        if self._use_pyvista and self._plotter is not None:
            if depth_idx < data.shape[0]:
                slice_data = data[depth_idx, :, :]

                # Yüzey oluştur
                x = np.arange(slice_data.shape[0])
                y = np.arange(slice_data.shape[1])
                x_grid, y_grid = np.meshgrid(x, y, indexing="ij")
                z_grid = np.full_like(x_grid, depth_idx, dtype=float)

                points = np.column_stack(
                    [x_grid.ravel(), z_grid.ravel(), y_grid.ravel()]
                )
                cloud = pv.PolyData(points)
                cloud["amplitude"] = slice_data.ravel()

                surface = cloud.delaunay_2d()
                self._plotter.add_mesh(
                    surface,
                    scalars="amplitude",
                    cmap=colormap,
                    opacity=0.7,
                    show_scalar_bar=False,
                )
                self._plotter.render()

    def add_isosurface(
        self,
        data: np.ndarray,
        iso_value: float = 0.5,
        color: str = "orange",
        opacity: float = 0.5,
    ) -> None:
        """
        İzo-yüzey ekler.

        Args:
            data: 3D veri dizisi
            iso_value: İzo değer
            color: Renk
            opacity: Saydamlık
        """
        if self._use_pyvista and self._plotter is not None:
            norm_data = np.abs(data.copy())
            max_val = np.max(norm_data)
            if max_val > 0:
                norm_data = norm_data / max_val

            grid = pv.ImageData(
                dimensions=data.shape,
                spacing=(1.0, 1.0, 1.0),
            )
            grid.point_data["amplitude"] = norm_data.flatten(order="F")

            try:
                contours = grid.contour([iso_value], scalars="amplitude")
                if contours.n_points > 0:
                    self._plotter.add_mesh(
                        contours,
                        color=color,
                        opacity=opacity,
                    )
                    self._plotter.render()
            except Exception:
                pass

    def clear(self) -> None:
        """3D sahneyi temizler."""
        if self._use_pyvista and self._plotter is not None:
            self._plotter.clear()
            self._plotter.add_axes()
        elif hasattr(self, "_gl_widget"):
            import pyqtgraph.opengl as gl

            items_to_remove = []
            for item in self._gl_widget.items:
                if not isinstance(item, gl.GLGridItem):
                    items_to_remove.append(item)
            for item in items_to_remove:
                self._gl_widget.removeItem(item)

    def set_view(self, view: str = "iso") -> None:
        """
        Kamera açısını ayarlar.

        Args:
            view: Görünüm tipi ('iso', 'top', 'front', 'side')
        """
        if self._use_pyvista and self._plotter is not None:
            if view == "top":
                self._plotter.view_xy()
            elif view == "front":
                self._plotter.view_xz()
            elif view == "side":
                self._plotter.view_yz()
            else:
                self._plotter.view_isometric()

    def get_volume_data(self) -> np.ndarray | None:
        """Mevcut hacim verisini döndürür."""
        return self._volume_data
