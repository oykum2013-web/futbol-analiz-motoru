"""
GPR Radar Yardımcı Fonksiyonlar
"""

import numpy as np


def depth_to_time(depth: float, velocity: float = 0.1) -> float:
    """
    Derinliği iki yönlü seyahat süresine dönüştürür.

    Args:
        depth: Derinlik (metre)
        velocity: Dalga hızı (m/ns)

    Returns:
        İki yönlü seyahat süresi (ns)
    """
    return 2.0 * depth / velocity


def time_to_depth(travel_time: float, velocity: float = 0.1) -> float:
    """
    İki yönlü seyahat süresini derinliğe dönüştürür.

    Args:
        travel_time: İki yönlü seyahat süresi (ns)
        velocity: Dalga hızı (m/ns)

    Returns:
        Derinlik (metre)
    """
    return travel_time * velocity / 2.0


def sample_to_depth(
    sample_idx: int, num_samples: int, max_depth: float
) -> float:
    """
    Örnek indeksini derinliğe dönüştürür.

    Args:
        sample_idx: Örnek indeksi
        num_samples: Toplam örnek sayısı
        max_depth: Maksimum derinlik (metre)

    Returns:
        Derinlik (metre)
    """
    return (sample_idx / num_samples) * max_depth


def normalize_data(data: np.ndarray) -> np.ndarray:
    """
    Veriyi 0-1 aralığına normalize eder.

    Args:
        data: Giriş verisi

    Returns:
        Normalize edilmiş veri
    """
    min_val = np.min(data)
    max_val = np.max(data)
    if max_val - min_val > 1e-10:
        return (data - min_val) / (max_val - min_val)
    return np.zeros_like(data)


def ricker_wavelet(
    freq: float, dt: float, length: int
) -> np.ndarray:
    """
    Ricker (Meksika şapkası) dalgacığı oluşturur.

    Args:
        freq: Merkez frekansı (Hz)
        dt: Zaman adımı (s)
        length: Dalgacık uzunluğu (örnek)

    Returns:
        Ricker dalgacığı
    """
    t = np.arange(length) * dt - (length // 2) * dt
    pi_f_t = np.pi * freq * t
    wavelet = (1 - 2 * pi_f_t**2) * np.exp(-(pi_f_t**2))
    return wavelet


def estimate_velocity(
    hyperbola_width: float, hyperbola_depth: float, trace_spacing: float
) -> float:
    """
    Hiperbol geometrisinden dalga hızını tahmin eder.

    Args:
        hyperbola_width: Hiperbol genişliği (iz sayısı)
        hyperbola_depth: Hiperbol derinliği (örnek)
        trace_spacing: İz aralığı (metre)

    Returns:
        Tahmini dalga hızı (m/ns)
    """
    x = hyperbola_width * trace_spacing / 2.0
    t0 = hyperbola_depth
    if t0 > 0:
        velocity = 2.0 * x / np.sqrt(t0**2)
        return velocity
    return 0.1  # varsayılan


def calculate_resolution(
    velocity: float, frequency: float
) -> dict[str, float]:
    """
    GPR çözünürlüğünü hesaplar.

    Args:
        velocity: Dalga hızı (m/ns)
        frequency: Anten frekansı (Hz)

    Returns:
        Dikey ve yatay çözünürlük değerleri (metre)
    """
    wavelength = velocity * 1e9 / frequency  # metre
    vertical_res = wavelength / 4.0
    horizontal_res = wavelength / 2.0

    return {
        "wavelength": wavelength,
        "vertical_resolution": vertical_res,
        "horizontal_resolution": horizontal_res,
    }
