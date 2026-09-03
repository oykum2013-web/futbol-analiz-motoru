import AsyncStorage from '@react-native-async-storage/async-storage';
import { useCallback, useEffect, useState } from 'react';
import { API_BASE_URL_STORAGE_KEY, DEFAULT_API_BASE_URL } from '../api/config';

export function useApiBaseUrl() {
  const [baseUrl, setBaseUrlState] = useState(DEFAULT_API_BASE_URL);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(API_BASE_URL_STORAGE_KEY).then((stored) => {
      if (stored) setBaseUrlState(stored);
      setLoaded(true);
    });
  }, []);

  const setBaseUrl = useCallback((value: string) => {
    const trimmed = value.trim();
    setBaseUrlState(trimmed);
    AsyncStorage.setItem(API_BASE_URL_STORAGE_KEY, trimmed);
  }, []);

  return { baseUrl, setBaseUrl, loaded };
}
