import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useState } from 'react';

const USAGE_STORAGE_KEY = 'daily_match_query_usage';

// Ücretsiz plan: günde bu kadar gerçek maç sorgusu (/match) hakkı.
// Demo bülten (/bulletin/demo) bu limite dahil değil, sınırsız.
export const FREE_DAILY_MATCH_QUERIES = 1;

function todayKey(): string {
  return new Date().toISOString().slice(0, 10); // YYYY-MM-DD
}

export function useDailyQueryLimit(limit: number = FREE_DAILY_MATCH_QUERIES) {
  const [usedToday, setUsedToday] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    AsyncStorage.getItem(USAGE_STORAGE_KEY).then((raw) => {
      if (raw) {
        const parsed = JSON.parse(raw) as { date: string; count: number };
        setUsedToday(parsed.date === todayKey() ? parsed.count : 0);
      }
      setLoading(false);
    });
  }, []);

  const recordUsage = useCallback(async () => {
    setUsedToday((prev) => {
      const next = prev + 1;
      AsyncStorage.setItem(USAGE_STORAGE_KEY, JSON.stringify({ date: todayKey(), count: next }));
      return next;
    });
  }, []);

  return {
    usedToday,
    limit,
    remaining: Math.max(0, limit - usedToday),
    limitReached: usedToday >= limit,
    recordUsage,
    loading,
  };
}
