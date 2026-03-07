"""
GPR Sinyal İşleme Modülü
Temel sinyal işleme fonksiyonları: filtreleme, kazanç, toprak ayarı, vb.
"""

import numpy as np
from scipy import signal as scipy_signal
from scipy.ndimage import uniform_filter1d


class SignalProcessor:
    """GPR sinyal işleme sınıfı."""

    def __init__(self, sample_rate: float = 1e9, num_samples: int = 512):
        self.sample_rate = sample_rate
        self.num_samples = num_samples
        self.time_axis = np.arange(num_samples) / sample_rate

    def remove_dc_offset(self, trace: np.ndarray) -> np.ndarray:
        """DC ofset kaldırma - her iz için ortalama değeri çıkarır."""
        return trace - np.mean(trace)

    def bandpass_filter(
        self,
        data: np.ndarray,
        low_freq: float = 100e6,
        high_freq: float = 800e6,
        order: int = 4,
    ) -> np.ndarray:
        """
        Bant geçiren filtre uygular.

        Args:
            data: Giriş verisi (tek iz veya 2D radargram)
            low_freq: Alt kesim frekansı (Hz)
            high_freq: Üst kesim frekansı (Hz)
            order: Filtre derecesi

        Returns:
            Filtrelenmiş veri
        """
        nyquist = self.sample_rate / 2.0
        low = low_freq / nyquist
        high = high_freq / nyquist

        low = max(low, 0.001)
        high = min(high, 0.999)

        if low >= high:
            return data

        b, a = scipy_signal.butter(order, [low, high], btype="band")

        if data.ndim == 1:
            return scipy_signal.filtfilt(b, a, data)
        elif data.ndim == 2:
            filtered = np.zeros_like(data)
            for i in range(data.shape[1]):
                filtered[:, i] = scipy_signal.filtfilt(b, a, data[:, i])
            return filtered
        return data

    def hilbert_transform(self, data: np.ndarray) -> np.ndarray:
        """
        Hilbert dönüşümü ile zarf algılama.

        Args:
            data: Giriş verisi

        Returns:
            Zarf (envelope) verisi
        """
        if data.ndim == 1:
            analytic = scipy_signal.hilbert(data)
            return np.abs(analytic)
        elif data.ndim == 2:
            envelope = np.zeros_like(data)
            for i in range(data.shape[1]):
                analytic = scipy_signal.hilbert(data[:, i])
                envelope[:, i] = np.abs(analytic)
            return envelope
        return data

    def moving_average(self, data: np.ndarray, window_size: int = 5) -> np.ndarray:
        """
        Hareketli ortalama filtresi.

        Args:
            data: Giriş verisi
            window_size: Pencere boyutu

        Returns:
            Filtrelenmiş veri
        """
        if data.ndim == 1:
            return uniform_filter1d(data, size=window_size)
        elif data.ndim == 2:
            result = np.zeros_like(data)
            for i in range(data.shape[1]):
                result[:, i] = uniform_filter1d(data[:, i], size=window_size)
            return result
        return data

    def stacking(self, data: np.ndarray, num_stacks: int = 4) -> np.ndarray:
        """
        İz istifleme (stacking) - gürültü azaltmak için ardışık izleri ortalar.

        Args:
            data: 2D radargram verisi (samples x traces)
            num_stacks: İstifleme sayısı

        Returns:
            İstiflenmiş veri
        """
        if data.ndim != 2 or data.shape[1] < num_stacks:
            return data

        num_output_traces = data.shape[1] // num_stacks
        stacked = np.zeros((data.shape[0], num_output_traces))

        for i in range(num_output_traces):
            start_idx = i * num_stacks
            end_idx = start_idx + num_stacks
            stacked[:, i] = np.mean(data[:, start_idx:end_idx], axis=1)

        return stacked

    def migration_kirchhoff(
        self, data: np.ndarray, velocity: float = 0.1
    ) -> np.ndarray:
        """
        Basitleştirilmiş Kirchhoff migrasyon algoritması.

        Args:
            data: 2D radargram verisi (samples x traces)
            velocity: Dalga hızı (m/ns)

        Returns:
            Migrasyon uygulanmış veri
        """
        if data.ndim != 2:
            return data

        n_samples, n_traces = data.shape
        migrated = np.zeros_like(data)
        dt = 1.0 / self.sample_rate * 1e9  # ns cinsinden

        for ix in range(n_traces):
            for it in range(n_samples):
                t0 = it * dt
                aperture = min(20, n_traces // 4)

                for jx in range(
                    max(0, ix - aperture), min(n_traces, ix + aperture + 1)
                ):
                    dx = abs(jx - ix) * 0.05  # iz aralığı metre cinsinden
                    t_mig = np.sqrt(t0**2 + (2 * dx / velocity) ** 2)
                    it_mig = int(t_mig / dt)

                    if 0 <= it_mig < n_samples:
                        migrated[it, ix] += data[it_mig, jx]

        # Normalize
        max_val = np.max(np.abs(migrated))
        if max_val > 0:
            migrated = migrated / max_val
        return migrated


class GroundBalance:
    """
    Otomatik Toprak Ayarı (Ground Balance) Sınıfı.
    Toprak mineralizasyonunu otomatik olarak kompanse eder.
    """

    def __init__(self):
        self.background_trace: np.ndarray | None = None
        self.calibration_traces: list[np.ndarray] = []
        self.is_calibrated: bool = False
        self.adaptation_rate: float = 0.05

    def calibrate(self, traces: np.ndarray) -> None:
        """
        Toprak kalibrasyon verisi toplar.

        Args:
            traces: Kalibrasyon izleri (samples x traces)
        """
        if traces.ndim == 1:
            self.calibration_traces.append(traces.copy())
        elif traces.ndim == 2:
            for i in range(traces.shape[1]):
                self.calibration_traces.append(traces[:, i].copy())

        if len(self.calibration_traces) >= 5:
            cal_array = np.array(self.calibration_traces)
            self.background_trace = np.mean(cal_array, axis=0)
            self.is_calibrated = True

    def apply(self, data: np.ndarray) -> np.ndarray:
        """
        Toprak ayarı uygular - arka plan çıkarma.

        Args:
            data: Giriş verisi (tek iz veya 2D radargram)

        Returns:
            Toprak ayarı uygulanmış veri
        """
        if not self.is_calibrated or self.background_trace is None:
            return self.auto_background_removal(data)

        if data.ndim == 1:
            bg = self.background_trace[: len(data)]
            return data - bg
        elif data.ndim == 2:
            result = np.zeros_like(data)
            bg = self.background_trace[: data.shape[0]]
            for i in range(data.shape[1]):
                result[:, i] = data[:, i] - bg
            return result
        return data

    def auto_background_removal(self, data: np.ndarray) -> np.ndarray:
        """
        Otomatik arka plan çıkarma - kalibrasyon olmadan.
        Her iz için ortalama iz değerini çıkarır.

        Args:
            data: 2D radargram verisi (samples x traces)

        Returns:
            Arka planı çıkarılmış veri
        """
        if data.ndim == 1:
            return data - np.mean(data)
        elif data.ndim == 2:
            mean_trace = np.mean(data, axis=1, keepdims=True)
            return data - mean_trace
        return data

    def adaptive_update(self, new_trace: np.ndarray) -> None:
        """
        Arka plan modelini adaptif olarak günceller.

        Args:
            new_trace: Yeni iz verisi
        """
        if self.background_trace is not None and len(new_trace) == len(
            self.background_trace
        ):
            self.background_trace = (
                1 - self.adaptation_rate
            ) * self.background_trace + self.adaptation_rate * new_trace

    def reset(self) -> None:
        """Kalibrasyon verilerini sıfırlar."""
        self.background_trace = None
        self.calibration_traces = []
        self.is_calibrated = False


class AutoGainControl:
    """
    Otomatik Kazanç Ayarı (AGC) Sınıfı.
    Derinliğe bağlı sinyal amplifikasyonunu otomatik yapar.
    """

    GAIN_MODE_LINEAR = "linear"
    GAIN_MODE_EXPONENTIAL = "exponential"
    GAIN_MODE_AGC = "agc"
    GAIN_MODE_CUSTOM = "custom"

    def __init__(self, num_samples: int = 512):
        self.num_samples = num_samples
        self.gain_mode: str = self.GAIN_MODE_EXPONENTIAL
        self.gain_factor: float = 2.0
        self.agc_window: int = 50
        self.custom_curve: np.ndarray | None = None
        self._gain_curve: np.ndarray | None = None

    def compute_gain_curve(self) -> np.ndarray:
        """
        Mevcut moda göre kazanç eğrisi hesaplar.

        Returns:
            Kazanç eğrisi dizisi
        """
        t = np.arange(self.num_samples, dtype=float)

        if self.gain_mode == self.GAIN_MODE_LINEAR:
            curve = 1.0 + self.gain_factor * t / self.num_samples
        elif self.gain_mode == self.GAIN_MODE_EXPONENTIAL:
            curve = np.exp(self.gain_factor * t / self.num_samples)
        elif self.gain_mode == self.GAIN_MODE_CUSTOM and self.custom_curve is not None:
            curve = self.custom_curve.copy()
            if len(curve) != self.num_samples:
                curve = np.interp(
                    np.linspace(0, 1, self.num_samples),
                    np.linspace(0, 1, len(curve)),
                    curve,
                )
        else:
            curve = np.ones(self.num_samples)

        self._gain_curve = curve
        return curve

    def apply_tvg(self, data: np.ndarray) -> np.ndarray:
        """
        Zamana Bağlı Kazanç (Time-Varying Gain) uygular.

        Args:
            data: Giriş verisi (tek iz veya 2D radargram)

        Returns:
            Kazanç uygulanmış veri
        """
        curve = self.compute_gain_curve()

        if data.ndim == 1:
            gain = curve[: len(data)]
            return data * gain
        elif data.ndim == 2:
            gain = curve[: data.shape[0]].reshape(-1, 1)
            return data * gain
        return data

    def apply_agc(self, data: np.ndarray) -> np.ndarray:
        """
        Otomatik Kazanç Kontrolü (AGC) uygular.
        Pencere tabanlı normalizasyon.

        Args:
            data: Giriş verisi

        Returns:
            AGC uygulanmış veri
        """
        if data.ndim == 1:
            return self._agc_trace(data)
        elif data.ndim == 2:
            result = np.zeros_like(data)
            for i in range(data.shape[1]):
                result[:, i] = self._agc_trace(data[:, i])
            return result
        return data

    def _agc_trace(self, trace: np.ndarray) -> np.ndarray:
        """
        Tek iz için AGC uygular.

        Args:
            trace: Tek iz verisi

        Returns:
            AGC uygulanmış iz
        """
        n = len(trace)
        result = np.zeros(n)
        half_window = self.agc_window // 2

        for i in range(n):
            start = max(0, i - half_window)
            end = min(n, i + half_window + 1)
            window_data = trace[start:end]
            rms = np.sqrt(np.mean(window_data**2))
            if rms > 1e-10:
                result[i] = trace[i] / rms
            else:
                result[i] = trace[i]

        return result

    def apply(self, data: np.ndarray) -> np.ndarray:
        """
        Seçili moda göre kazanç uygular.

        Args:
            data: Giriş verisi

        Returns:
            Kazanç uygulanmış veri
        """
        if self.gain_mode == self.GAIN_MODE_AGC:
            return self.apply_agc(data)
        else:
            return self.apply_tvg(data)

    def auto_adjust(self, data: np.ndarray) -> None:
        """
        Veri özelliklerine göre kazanç parametrelerini otomatik ayarlar.

        Args:
            data: Referans verisi
        """
        if data.ndim == 1:
            trace = data
        elif data.ndim == 2:
            trace = np.mean(np.abs(data), axis=1)
        else:
            return

        # İlk ve son çeyreğin ortalama genliklerini karşılaştır
        n = len(trace)
        quarter = n // 4
        early_amp = np.mean(np.abs(trace[:quarter])) if quarter > 0 else 1.0
        late_amp = np.mean(np.abs(trace[-quarter:])) if quarter > 0 else 1.0

        if early_amp > 1e-10 and late_amp > 1e-10:
            ratio = early_amp / late_amp
            # Ratio'ya göre kazanç faktörünü ayarla
            self.gain_factor = min(max(np.log(ratio + 1), 0.5), 5.0)
        else:
            self.gain_factor = 2.0

    def set_custom_curve(self, curve: np.ndarray) -> None:
        """
        Özel kazanç eğrisi ayarlar.

        Args:
            curve: Özel kazanç eğrisi
        """
        self.custom_curve = curve.copy()
        self.gain_mode = self.GAIN_MODE_CUSTOM

    def get_current_curve(self) -> np.ndarray:
        """Mevcut kazanç eğrisini döndürür."""
        if self._gain_curve is None:
            return self.compute_gain_curve()
        return self._gain_curve.copy()
