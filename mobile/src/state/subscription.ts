import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useState } from 'react';

const PREMIUM_STORAGE_KEY = 'is_premium';

/**
 * Gerçek satın alma entegrasyonu (RevenueCat + App Store/Play Store IAP)
 * henüz bağlı değil — abonelik ödemesi bu platformlarda zorunlu olarak
 * uygulama içi satın alma üzerinden alınmalı. `purchase()` şimdilik yerel
 * bir bayrağı set eden TEST/MOCK bir akıştır, gerçek ödeme almaz. Mağaza
 * hesapları hazır olduğunda bu dosyanın içi RevenueCat SDK çağrılarıyla
 * değiştirilmeli; dışa açılan arayüz (isPremium/purchase/restore) aynı kalabilir.
 */
export function useSubscription() {
  const [isPremium, setIsPremium] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    AsyncStorage.getItem(PREMIUM_STORAGE_KEY).then((value) => {
      setIsPremium(value === 'true');
      setLoading(false);
    });
  }, []);

  const purchase = useCallback(async () => {
    await AsyncStorage.setItem(PREMIUM_STORAGE_KEY, 'true');
    setIsPremium(true);
  }, []);

  const restore = useCallback(async () => {
    const value = await AsyncStorage.getItem(PREMIUM_STORAGE_KEY);
    setIsPremium(value === 'true');
  }, []);

  return { isPremium, loading, purchase, restore };
}
