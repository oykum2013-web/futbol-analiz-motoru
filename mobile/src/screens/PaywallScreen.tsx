import { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

type Props = {
  visible: boolean;
  onClose: () => void;
  onPurchase: () => Promise<void>;
};

const BENEFITS = [
  'Sınırsız gerçek maç sorgusu (günlük 1 sorgu limiti kalkar)',
  'Tüm ligler için tam analiz',
  'Detaylı gerekçe: form, H2H, kadro ve piyasa kırılımı',
  'Eksik veri dökümü ("veri yok" uyarıları) tüm alt başlıklarıyla',
];

export default function PaywallScreen({ visible, onClose, onPurchase }: Props) {
  const [purchasing, setPurchasing] = useState(false);

  const handlePurchase = async () => {
    setPurchasing(true);
    try {
      await onPurchase();
    } finally {
      setPurchasing(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={styles.backdrop}>
        <View style={styles.sheet}>
          <ScrollView contentContainerStyle={styles.scrollContent}>
            <Text style={styles.title}>Premium'a Geç</Text>
            <Text style={styles.subtitle}>
              Ücretsiz plandaki günlük gerçek maç sorgusu hakkını kullandın veya tam
              analiz görmek istiyorsun.
            </Text>

            {BENEFITS.map((benefit) => (
              <View key={benefit} style={styles.benefitRow}>
                <Text style={styles.benefitCheck}>✓</Text>
                <Text style={styles.benefitText}>{benefit}</Text>
              </View>
            ))}

            <View style={styles.priceBox}>
              <Text style={styles.priceValue}>Aylık abonelik</Text>
              <Text style={styles.priceNote}>
                Fiyat, App Store / Google Play üzerinden ülkene göre gösterilecek
                (yerel fiyatlandırma mağaza tarafında ayarlanır).
              </Text>
            </View>

            <Pressable
              style={[styles.purchaseButton, purchasing && styles.purchaseButtonDisabled]}
              onPress={handlePurchase}
              disabled={purchasing}
            >
              <Text style={styles.purchaseButtonText}>
                {purchasing ? 'İşleniyor…' : 'Abone Ol (TEST)'}
              </Text>
            </Pressable>

            <Text style={styles.testNote}>
              ⚠️ TEST MODU: Gerçek ödeme entegrasyonu (RevenueCat / App Store / Play
              Store) henüz bağlı değil. Bu buton yalnızca Premium durumunu cihazda
              yerel olarak işaretler, ücret tahsil etmez.
            </Text>

            <Pressable onPress={onClose} style={styles.dismissButton}>
              <Text style={styles.dismissButtonText}>Şimdi Değil</Text>
            </Pressable>
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: '#0b1220',
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    maxHeight: '85%',
  },
  scrollContent: {
    padding: 24,
    paddingBottom: 36,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 13,
    color: '#8fa3c0',
    marginBottom: 20,
    lineHeight: 19,
  },
  benefitRow: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  benefitCheck: {
    color: '#2e7d32',
    fontWeight: '700',
    marginRight: 8,
  },
  benefitText: {
    flex: 1,
    color: '#d3ddeb',
    fontSize: 13,
    lineHeight: 18,
  },
  priceBox: {
    backgroundColor: '#141d2e',
    borderRadius: 10,
    padding: 14,
    marginTop: 12,
    marginBottom: 20,
  },
  priceValue: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
    marginBottom: 4,
  },
  priceNote: {
    color: '#5a6472',
    fontSize: 11,
    lineHeight: 15,
  },
  purchaseButton: {
    backgroundColor: '#2e7d32',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
    marginBottom: 12,
  },
  purchaseButtonDisabled: {
    opacity: 0.6,
  },
  purchaseButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  testNote: {
    color: '#f0b357',
    fontSize: 11,
    lineHeight: 15,
    marginBottom: 16,
  },
  dismissButton: {
    alignItems: 'center',
  },
  dismissButtonText: {
    color: '#8fa3c0',
    fontSize: 14,
  },
});
