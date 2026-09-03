import { CONFIDENCE_COLORS, confidenceColor } from '../MatchCard';

// ajan_ordusu/agents/prediction.py'nin üretebileceği tüm confidence
// değerleri (bkz. o dosyadaki confidence atamaları). Buradaki liste
// güncel değilse bu test onu yakalamalı.
const BACKEND_CONFIDENCE_VALUES = ['Orta', 'Düşük', 'Çok Düşük', 'Orta-Yüksek', 'Yetersiz Veri'];

const FALLBACK_COLOR = '#5a6472';

describe('MatchCard confidenceColor', () => {
  it('backend’in üretebileceği her confidence değeri için nötr fallback rengi DEĞİL, kendine özgü bir renk döner', () => {
    for (const value of BACKEND_CONFIDENCE_VALUES) {
      if (value === 'Yetersiz Veri') continue; // bu değerin fallback rengiyle aynı olması kasıtlı
      expect(confidenceColor(value)).not.toBe(FALLBACK_COLOR);
    }
  });

  it('her backend confidence değeri CONFIDENCE_COLORS haritasında tanımlı', () => {
    for (const value of BACKEND_CONFIDENCE_VALUES) {
      expect(CONFIDENCE_COLORS[value]).toBeDefined();
    }
  });

  it('bilinmeyen bir değer için nötr fallback rengi döner (uygulama çökmez)', () => {
    expect(confidenceColor('beklenmeyen-deger')).toBe(FALLBACK_COLOR);
  });

  it('"Yetersiz Veri" için nötr/uyarı rengi döner', () => {
    expect(confidenceColor('Yetersiz Veri')).toBe(FALLBACK_COLOR);
  });
});
