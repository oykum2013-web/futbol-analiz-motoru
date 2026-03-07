"""
GPR Veri Yönetimi Modülü
Tarama verilerinin kaydedilmesi, yüklenmesi ve dışa aktarılması.
"""

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import h5py
import numpy as np


@dataclass
class ScanMetadata:
    """Tarama meta verileri."""

    scan_id: str = ""
    date: str = ""
    operator: str = ""
    location: str = ""
    device: str = "Tork Pro 300"
    sample_rate: float = 1e9
    num_samples: int = 512
    num_traces: int = 0
    trace_spacing: float = 0.05  # metre
    depth_range: float = 5.0  # metre
    antenna_freq: float = 300e6  # Hz
    soil_type: str = "Bilinmiyor"
    notes: str = ""
    settings: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Meta verileri sözlüğe dönüştürür."""
        return {
            "scan_id": self.scan_id,
            "date": self.date,
            "operator": self.operator,
            "location": self.location,
            "device": self.device,
            "sample_rate": self.sample_rate,
            "num_samples": self.num_samples,
            "num_traces": self.num_traces,
            "trace_spacing": self.trace_spacing,
            "depth_range": self.depth_range,
            "antenna_freq": self.antenna_freq,
            "soil_type": self.soil_type,
            "notes": self.notes,
            "settings": self.settings,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ScanMetadata":
        """Sözlükten meta veri nesnesi oluşturur."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class ScanSession:
    """Tek bir tarama oturumu."""

    def __init__(self, metadata: ScanMetadata | None = None):
        self.metadata = metadata or ScanMetadata()
        if not self.metadata.scan_id:
            self.metadata.scan_id = f"scan_{int(time.time())}"
        if not self.metadata.date:
            self.metadata.date = time.strftime("%Y-%m-%d %H:%M:%S")

        self.raw_data: np.ndarray | None = None
        self.processed_data: np.ndarray | None = None
        self.traces: list[np.ndarray] = []
        self.scan_lines: list[np.ndarray] = []  # 3D tarama çizgileri
        self.annotations: list[dict[str, Any]] = []

    def add_trace(self, trace: np.ndarray) -> None:
        """Yeni iz ekler."""
        self.traces.append(trace.copy())
        self.metadata.num_traces = len(self.traces)

    def add_scan_line(self, line_data: np.ndarray) -> None:
        """3D tarama için yeni tarama çizgisi ekler."""
        self.scan_lines.append(line_data.copy())

    def get_radargram(self) -> np.ndarray:
        """Tüm izleri 2D radargram olarak döndürür."""
        if self.raw_data is not None:
            return self.raw_data
        if len(self.traces) > 0:
            return np.column_stack(self.traces)
        return np.array([])

    def get_3d_volume(self) -> np.ndarray | None:
        """3D veri hacmini döndürür."""
        if len(self.scan_lines) > 0:
            try:
                return np.stack(self.scan_lines, axis=2)
            except ValueError:
                return None
        return None

    def add_annotation(
        self, trace_idx: int, sample_idx: int, text: str, ann_type: str = "marker"
    ) -> None:
        """Taramaya açıklama ekler."""
        self.annotations.append(
            {
                "trace_idx": trace_idx,
                "sample_idx": sample_idx,
                "text": text,
                "type": ann_type,
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )


class DataManager:
    """Veri kaydetme, yükleme ve dışa aktarma yöneticisi."""

    def __init__(self, data_dir: str = "gpr_data"):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

    def save_session(self, session: ScanSession, filename: str = "") -> str:
        """
        Tarama oturumunu HDF5 formatında kaydeder.

        Args:
            session: Kaydedilecek tarama oturumu
            filename: Dosya adı (boşsa otomatik oluşturulur)

        Returns:
            Kaydedilen dosyanın yolu
        """
        if not filename:
            filename = f"{session.metadata.scan_id}.h5"

        filepath = os.path.join(self.data_dir, filename)

        with h5py.File(filepath, "w") as f:
            # Meta verileri kaydet
            meta_group = f.create_group("metadata")
            meta_dict = session.metadata.to_dict()
            meta_group.attrs["json"] = json.dumps(meta_dict, ensure_ascii=False)

            # Ham veri kaydet
            radargram = session.get_radargram()
            if radargram.size > 0:
                f.create_dataset("raw_data", data=radargram, compression="gzip")

            # İşlenmiş veri kaydet
            if session.processed_data is not None:
                f.create_dataset(
                    "processed_data", data=session.processed_data, compression="gzip"
                )

            # 3D veri kaydet
            volume = session.get_3d_volume()
            if volume is not None:
                f.create_dataset("volume_3d", data=volume, compression="gzip")

            # Açıklamalar kaydet
            if session.annotations:
                ann_group = f.create_group("annotations")
                ann_group.attrs["json"] = json.dumps(
                    session.annotations, ensure_ascii=False
                )

        return filepath

    def load_session(self, filepath: str) -> ScanSession:
        """
        HDF5 dosyasından tarama oturumu yükler.

        Args:
            filepath: Dosya yolu

        Returns:
            Yüklenen tarama oturumu
        """
        with h5py.File(filepath, "r") as f:
            # Meta verileri yükle
            meta_json = f["metadata"].attrs["json"]
            meta_dict = json.loads(meta_json)
            metadata = ScanMetadata.from_dict(meta_dict)

            session = ScanSession(metadata=metadata)

            # Ham veri yükle
            if "raw_data" in f:
                session.raw_data = np.array(f["raw_data"])

            # İşlenmiş veri yükle
            if "processed_data" in f:
                session.processed_data = np.array(f["processed_data"])

            # 3D veri yükle
            if "volume_3d" in f:
                volume = np.array(f["volume_3d"])
                for i in range(volume.shape[2]):
                    session.scan_lines.append(volume[:, :, i])

            # Açıklamalar yükle
            if "annotations" in f:
                ann_json = f["annotations"].attrs["json"]
                session.annotations = json.loads(ann_json)

        return session

    def export_csv(self, session: ScanSession, filepath: str) -> None:
        """Radargram verisini CSV formatında dışa aktarır."""
        radargram = session.get_radargram()
        if radargram.size > 0:
            np.savetxt(filepath, radargram, delimiter=",", fmt="%.6f")

    def export_numpy(self, session: ScanSession, filepath: str) -> None:
        """Radargram verisini NumPy formatında dışa aktarır."""
        radargram = session.get_radargram()
        if radargram.size > 0:
            np.save(filepath, radargram)

    def export_image(
        self, session: ScanSession, filepath: str, dpi: int = 150
    ) -> None:
        """Radargram verisini görüntü olarak dışa aktarır."""
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        radargram = session.get_radargram()
        if radargram.size > 0:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.imshow(
                radargram, aspect="auto", cmap="seismic", interpolation="bilinear"
            )
            ax.set_xlabel("İz Numarası")
            ax.set_ylabel("Örnek Numarası")
            ax.set_title(f"GPR Radargram - {session.metadata.scan_id}")
            fig.savefig(filepath, dpi=dpi, bbox_inches="tight")
            plt.close(fig)

    def list_sessions(self) -> list[str]:
        """Kayıtlı tarama oturumlarını listeler."""
        sessions = []
        if os.path.exists(self.data_dir):
            for f in os.listdir(self.data_dir):
                if f.endswith(".h5"):
                    sessions.append(os.path.join(self.data_dir, f))
        return sorted(sessions)
