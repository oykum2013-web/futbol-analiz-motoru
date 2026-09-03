export const API_BASE_URL_STORAGE_KEY = 'api_base_url';

// Geliştirme sırasında `uvicorn ajan_ordusu.api:app --host 0.0.0.0 --port 8000`
// ile başlatılan sunucunun adresi. Fiziksel bir cihazdan test ederken
// bilgisayarın LAN IP'si (ör. http://192.168.1.23:8000) gerekir; ekrandaki
// "API Adresi" alanından değiştirilip kalıcı olarak saklanır.
export const DEFAULT_API_BASE_URL =
  process.env.EXPO_PUBLIC_API_BASE_URL || 'http://localhost:8000';
