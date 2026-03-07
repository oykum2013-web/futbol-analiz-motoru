# GPR Radar - Tork Pro 300

Farmet Teknoloji Tork Pro 300 GPR (Yer Radarı) cihazı için geliştirilmiş profesyonel analiz yazılımı.

## Özellikler

### Gerçek Zamanlı 3D Analiz
- B-scan (radargram) görüntüleme
- C-scan (derinlik kesit) görüntüleme
- 3D hacimsel veri görselleştirme
- İzo-yüzey ve derinlik kesit analizi
- İnteraktif döndürme, yakınlaştırma, kaydırma

### Otomatik Toprak Ayarı (Ground Balance)
- Otomatik toprak mineralizasyonu kompanzasyonu
- Adaptif arka plan çıkarma
- Manuel kalibrasyon desteği
- Farklı toprak tipleri için optimizasyon

### Otomatik Kazanç Kontrolü (AGC)
- Zamana bağlı kazanç (TVG)
- Üstel / doğrusal / AGC modları
- Otomatik kazanç parametresi ayarlama
- Özel kazanç eğrisi desteği

### Tork Pro 300 Entegrasyonu
- Seri port üzerinden cihaz iletişimi
- Otomatik port algılama
- Gerçek zamanlı veri akışı
- Simülasyon modu (cihaz olmadan test)

### Sinyal İşleme
- Bant geçiren filtreleme
- Hilbert dönüşümü (zarf algılama)
- DC ofset kaldırma
- Kirchhoff migrasyon
- İz istifleme (stacking)

### Veri Yönetimi
- HDF5 formatında kaydetme/yükleme
- CSV, NumPy, görüntü formatlarında dışa aktarma
- Tarama notları ve meta veri desteği

## Kurulum

### Gereksinimler
- Python 3.10+
- PyQt5
- NumPy, SciPy
- PyQtGraph
- PyVista (opsiyonel, 3D görselleştirme için)

### Yükleme

```bash
# Depoyu klonlayın
git clone <repo-url>
cd gpr-radar-tork-pro-300

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# Uygulamayı çalıştırın
python main.py
```

## Kullanım

1. **Bağlantı**: Cihaz panelinden Tork Pro 300'e bağlanın veya "Simülasyon" modunu seçin
2. **Tarama**: "Taramayı Başlat" butonuna tıklayın
3. **Analiz**: Sinyal işleme parametrelerini ayarlayın (toprak ayarı, kazanç, filtreler)
4. **3D Görüntüleme**: "3D Güncelle" butonuyla 3D görselleştirmeyi aktifleştirin
5. **Kaydet**: Taramayı HDF5 formatında kaydedin veya farklı formatlarda dışa aktarın

## Proje Yapısı

```
gpr-radar-tork-pro-300/
├── main.py                          # Ana giriş noktası
├── requirements.txt                 # Bağımlılıklar
├── gpr_radar/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── signal_processing.py     # Sinyal işleme, toprak ayarı, kazanç
│   │   └── data_manager.py          # Veri kaydetme/yükleme
│   ├── device/
│   │   ├── __init__.py
│   │   └── tork_pro_300.py          # Cihaz sürücüsü ve simülasyon
│   ├── visualization/
│   │   ├── __init__.py
│   │   ├── radar_plots.py           # 2D radargram/A-scan görüntüleme
│   │   └── viewer_3d.py             # 3D hacimsel görselleştirme
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── main_window.py           # Ana pencere
│   │   └── control_panel.py         # Kontrol panelleri
│   └── utils/
│       ├── __init__.py
│       └── helpers.py               # Yardımcı fonksiyonlar
```

## Lisans

Farmet Teknoloji &copy; 2024
