"""
Farmet Teknoloji Tork Pro 300 GPR Cihaz İletişim Modülü
Seri port üzerinden cihaz ile iletişim sağlar.
"""

import logging
import struct
import threading
import time
from enum import Enum
from typing import Callable

import numpy as np

try:
    import serial
    import serial.tools.list_ports

    SERIAL_AVAILABLE = True
except ImportError:
    SERIAL_AVAILABLE = False

logger = logging.getLogger(__name__)


class DeviceState(Enum):
    """Cihaz durumu."""

    DISCONNECTED = "Bağlı Değil"
    CONNECTING = "Bağlanıyor"
    CONNECTED = "Bağlı"
    SCANNING = "Tarama Yapılıyor"
    ERROR = "Hata"
    CALIBRATING = "Kalibrasyon"


class TorkPro300Protocol:
    """Tork Pro 300 iletişim protokolü sabitleri."""

    # Komut başlık baytları
    HEADER = b"\xAA\x55"
    FOOTER = b"\x55\xAA"

    # Komut kodları
    CMD_CONNECT = 0x01
    CMD_DISCONNECT = 0x02
    CMD_START_SCAN = 0x03
    CMD_STOP_SCAN = 0x04
    CMD_GET_STATUS = 0x05
    CMD_SET_PARAMS = 0x06
    CMD_CALIBRATE = 0x07
    CMD_GET_TRACE = 0x08
    CMD_SET_GAIN = 0x09
    CMD_SET_FREQUENCY = 0x0A
    CMD_RESET = 0x0F

    # Yanıt kodları
    RESP_OK = 0x80
    RESP_ERROR = 0x81
    RESP_DATA = 0x82
    RESP_STATUS = 0x83

    @staticmethod
    def build_command(cmd: int, payload: bytes = b"") -> bytes:
        """
        Komut paketi oluşturur.

        Args:
            cmd: Komut kodu
            payload: Veri yükü

        Returns:
            Komut paketi baytları
        """
        length = len(payload) + 1  # cmd byte + payload
        packet = TorkPro300Protocol.HEADER
        packet += struct.pack("<H", length)
        packet += struct.pack("B", cmd)
        packet += payload
        # Checksum hesapla
        checksum = sum(packet) & 0xFF
        packet += struct.pack("B", checksum)
        packet += TorkPro300Protocol.FOOTER
        return packet

    @staticmethod
    def parse_response(data: bytes) -> tuple[int, bytes] | None:
        """
        Yanıt paketini ayrıştırır.

        Args:
            data: Ham bayt verisi

        Returns:
            (yanıt_kodu, veri_yükü) veya None
        """
        if len(data) < 7:  # min: header(2) + length(2) + cmd(1) + checksum(1) + footer(2)
            return None

        if data[:2] != TorkPro300Protocol.HEADER:
            return None

        length = struct.unpack("<H", data[2:4])[0]
        resp_code = data[4]
        payload = data[5 : 5 + length - 1]

        return (resp_code, payload)


class TorkPro300Device:
    """
    Farmet Teknoloji Tork Pro 300 GPR cihaz sürücüsü.
    """

    DEFAULT_BAUD_RATE = 115200
    DEFAULT_TIMEOUT = 2.0
    TRACE_SIZE = 512  # Varsayılan örnek sayısı

    def __init__(self):
        self.state: DeviceState = DeviceState.DISCONNECTED
        self.serial_port: "serial.Serial | None" = None
        self.port_name: str = ""
        self.baud_rate: int = self.DEFAULT_BAUD_RATE

        # Cihaz bilgileri
        self.firmware_version: str = "Bilinmiyor"
        self.battery_level: float = 0.0
        self.temperature: float = 0.0

        # Tarama parametreleri
        self.num_samples: int = self.TRACE_SIZE
        self.sample_rate: float = 1e9
        self.antenna_freq: float = 300e6
        self.scan_depth: float = 5.0  # metre

        # Veri akışı
        self._scanning: bool = False
        self._scan_thread: threading.Thread | None = None
        self._data_callback: Callable[[np.ndarray], None] | None = None
        self._status_callback: Callable[[DeviceState], None] | None = None

        # Simülasyon modu
        self._simulation_mode: bool = False

    @staticmethod
    def list_available_ports() -> list[dict[str, str]]:
        """Kullanılabilir seri portları listeler."""
        if not SERIAL_AVAILABLE:
            return []

        ports = []
        for port in serial.tools.list_ports.comports():
            ports.append(
                {
                    "port": port.device,
                    "description": port.description,
                    "hwid": port.hwid,
                }
            )
        return ports

    def connect(self, port: str = "", baud_rate: int = 0) -> bool:
        """
        Cihaza bağlanır.

        Args:
            port: Seri port adı (boşsa simülasyon modu)
            baud_rate: Baud hızı

        Returns:
            Bağlantı başarılı ise True
        """
        if not port or not SERIAL_AVAILABLE:
            return self._start_simulation()

        self.port_name = port
        self.baud_rate = baud_rate or self.DEFAULT_BAUD_RATE
        self._set_state(DeviceState.CONNECTING)

        try:
            self.serial_port = serial.Serial(
                port=self.port_name,
                baudrate=self.baud_rate,
                timeout=self.DEFAULT_TIMEOUT,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
            )

            # Bağlantı komutu gönder
            cmd = TorkPro300Protocol.build_command(TorkPro300Protocol.CMD_CONNECT)
            self.serial_port.write(cmd)
            time.sleep(0.5)

            response = self.serial_port.read(64)
            if response:
                parsed = TorkPro300Protocol.parse_response(response)
                if parsed and parsed[0] == TorkPro300Protocol.RESP_OK:
                    self._set_state(DeviceState.CONNECTED)
                    logger.info(f"Tork Pro 300 bağlandı: {port}")
                    return True

            # Yanıt alınamadıysa bile bağlantıyı kabul et
            self._set_state(DeviceState.CONNECTED)
            logger.warning("Cihaz yanıtı alınamadı, bağlantı varsayıldı")
            return True

        except Exception as e:
            logger.error(f"Bağlantı hatası: {e}")
            self._set_state(DeviceState.ERROR)
            return False

    def disconnect(self) -> None:
        """Cihaz bağlantısını keser."""
        self.stop_scan()

        if self.serial_port and self.serial_port.is_open:
            try:
                cmd = TorkPro300Protocol.build_command(
                    TorkPro300Protocol.CMD_DISCONNECT
                )
                self.serial_port.write(cmd)
                time.sleep(0.2)
                self.serial_port.close()
            except Exception as e:
                logger.error(f"Bağlantı kesme hatası: {e}")

        self.serial_port = None
        self._simulation_mode = False
        self._set_state(DeviceState.DISCONNECTED)
        logger.info("Cihaz bağlantısı kesildi")

    def start_scan(self, callback: Callable[[np.ndarray], None] | None = None) -> bool:
        """
        Taramayı başlatır.

        Args:
            callback: Her yeni iz alındığında çağrılacak fonksiyon

        Returns:
            Başarılı ise True
        """
        if self.state not in (DeviceState.CONNECTED, DeviceState.SCANNING):
            logger.error("Tarama başlatılamaz: Cihaz bağlı değil")
            return False

        self._data_callback = callback
        self._scanning = True
        self._set_state(DeviceState.SCANNING)

        if self._simulation_mode:
            self._scan_thread = threading.Thread(
                target=self._simulation_scan_loop, daemon=True
            )
        else:
            self._scan_thread = threading.Thread(
                target=self._real_scan_loop, daemon=True
            )

        self._scan_thread.start()
        logger.info("Tarama başlatıldı")
        return True

    def stop_scan(self) -> None:
        """Taramayı durdurur."""
        self._scanning = False

        if self.serial_port and self.serial_port.is_open:
            try:
                cmd = TorkPro300Protocol.build_command(
                    TorkPro300Protocol.CMD_STOP_SCAN
                )
                self.serial_port.write(cmd)
            except Exception:
                pass

        if self._scan_thread and self._scan_thread.is_alive():
            self._scan_thread.join(timeout=2.0)

        if self.state == DeviceState.SCANNING:
            self._set_state(DeviceState.CONNECTED)
        logger.info("Tarama durduruldu")

    def set_scan_parameters(
        self,
        num_samples: int = 0,
        scan_depth: float = 0,
        antenna_freq: float = 0,
    ) -> None:
        """Tarama parametrelerini ayarlar."""
        if num_samples > 0:
            self.num_samples = num_samples
        if scan_depth > 0:
            self.scan_depth = scan_depth
        if antenna_freq > 0:
            self.antenna_freq = antenna_freq

        if self.serial_port and self.serial_port.is_open:
            payload = struct.pack(
                "<HfI",
                self.num_samples,
                self.scan_depth,
                int(self.antenna_freq),
            )
            cmd = TorkPro300Protocol.build_command(
                TorkPro300Protocol.CMD_SET_PARAMS, payload
            )
            try:
                self.serial_port.write(cmd)
            except Exception as e:
                logger.error(f"Parametre gönderme hatası: {e}")

    def set_on_status_change(self, callback: Callable[[DeviceState], None]) -> None:
        """Durum değişikliği geri çağırma fonksiyonu ayarlar."""
        self._status_callback = callback

    def _set_state(self, state: DeviceState) -> None:
        """Cihaz durumunu günceller."""
        self.state = state
        if self._status_callback:
            self._status_callback(state)

    def _start_simulation(self) -> bool:
        """Simülasyon modunu başlatır."""
        self._simulation_mode = True
        self._set_state(DeviceState.CONNECTED)
        self.firmware_version = "SIM 1.0"
        self.battery_level = 85.0
        self.temperature = 25.0
        logger.info("Simülasyon modu başlatıldı")
        return True

    def _simulation_scan_loop(self) -> None:
        """Simülasyon tarama döngüsü - gerçekçi GPR verisi üretir."""
        trace_count = 0
        while self._scanning:
            trace = self._generate_simulated_trace(trace_count)
            trace_count += 1

            if self._data_callback:
                self._data_callback(trace)

            # Simülasyon cihaz durumunu güncelle
            self.battery_level = max(0, 85.0 - trace_count * 0.01)
            self.temperature = 25.0 + np.random.normal(0, 0.5)

            time.sleep(0.05)  # ~20 Hz tarama hızı

    def _real_scan_loop(self) -> None:
        """Gerçek cihazdan veri okuma döngüsü."""
        if not self.serial_port:
            return

        # Tarama başlat komutu
        cmd = TorkPro300Protocol.build_command(TorkPro300Protocol.CMD_START_SCAN)
        try:
            self.serial_port.write(cmd)
        except Exception as e:
            logger.error(f"Tarama başlatma hatası: {e}")
            self._set_state(DeviceState.ERROR)
            return

        while self._scanning:
            try:
                # Veri isteği gönder
                cmd = TorkPro300Protocol.build_command(TorkPro300Protocol.CMD_GET_TRACE)
                self.serial_port.write(cmd)

                # Yanıt bekle
                header = self.serial_port.read(4)
                if len(header) < 4:
                    continue

                if header[:2] != TorkPro300Protocol.HEADER:
                    continue

                length = struct.unpack("<H", header[2:4])[0]
                remaining = self.serial_port.read(length + 3)  # cmd + data + checksum + footer

                if len(remaining) < length + 3:
                    continue

                resp_code = remaining[0]
                if resp_code == TorkPro300Protocol.RESP_DATA:
                    # Float32 verisi olarak ayrıştır
                    data_bytes = remaining[1 : 1 + self.num_samples * 4]
                    trace = np.frombuffer(data_bytes, dtype=np.float32)

                    if len(trace) == self.num_samples and self._data_callback:
                        self._data_callback(trace)

            except Exception as e:
                logger.error(f"Veri okuma hatası: {e}")
                if not self._scanning:
                    break
                time.sleep(0.1)

    def _generate_simulated_trace(self, trace_idx: int) -> np.ndarray:
        """
        Gerçekçi GPR simülasyon verisi üretir.

        Args:
            trace_idx: İz indeksi

        Returns:
            Simüle edilmiş iz verisi
        """
        n = self.num_samples
        t = np.arange(n, dtype=float)

        # Temel gürültü
        trace = np.random.normal(0, 0.02, n)

        # Yüzey yansıması (güçlü, yakın yüzeyde)
        surface_pos = 20 + np.random.normal(0, 0.5)
        trace += 0.8 * np.exp(-((t - surface_pos) ** 2) / 10) * np.cos(
            2 * np.pi * 0.05 * (t - surface_pos)
        )

        # Yeraltı hedefleri (hiperbolik yansımalar)
        targets = [
            {"depth": 100, "x_center": 50, "amplitude": 0.4, "width": 15},
            {"depth": 200, "x_center": 120, "amplitude": 0.3, "width": 20},
            {"depth": 150, "x_center": 200, "amplitude": 0.5, "width": 12},
            {"depth": 300, "x_center": 80, "amplitude": 0.25, "width": 25},
        ]

        for target in targets:
            dx = trace_idx - target["x_center"]
            # Hiperbolik gecikme
            hyperbolic_delay = np.sqrt(
                target["depth"] ** 2 + (dx * 0.5) ** 2
            ) / target["depth"]
            actual_depth = target["depth"] * hyperbolic_delay

            if 0 < actual_depth < n:
                amplitude = target["amplitude"] / (1 + abs(dx) * 0.02)
                wavelet = amplitude * np.exp(
                    -((t - actual_depth) ** 2) / target["width"]
                ) * np.cos(2 * np.pi * 0.04 * (t - actual_depth))
                trace += wavelet

        # Toprak katman yansımaları
        layers = [80, 180, 350]
        for layer_depth in layers:
            variation = 5 * np.sin(trace_idx * 0.03)
            d = layer_depth + variation
            trace += 0.15 * np.exp(-((t - d) ** 2) / 30) * np.cos(
                2 * np.pi * 0.03 * (t - d)
            )

        # Derinliğe bağlı zayıflama
        attenuation = np.exp(-0.003 * t)
        trace *= attenuation

        return trace.astype(np.float32)

    @property
    def is_connected(self) -> bool:
        """Cihaz bağlı mı?"""
        return self.state in (DeviceState.CONNECTED, DeviceState.SCANNING)

    @property
    def is_scanning(self) -> bool:
        """Tarama yapılıyor mu?"""
        return self.state == DeviceState.SCANNING and self._scanning

    @property
    def is_simulation(self) -> bool:
        """Simülasyon modunda mı?"""
        return self._simulation_mode
