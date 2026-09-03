import { useCallback, useEffect, useState } from 'react';
import {
  ActivityIndicator,
  Pressable,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { ApiError, fetchBulletinDemo, fetchMatch } from '../api/client';
import type { BulletinResponse } from '../api/types';
import { useApiBaseUrl } from '../hooks/useApiBaseUrl';
import { useDailyQueryLimit } from '../state/dailyUsage';
import { useSubscription } from '../state/subscription';
import MatchCard from '../components/MatchCard';
import PaywallScreen from './PaywallScreen';

const EMPTY_MATCH_FORM = {
  homeTeamId: '',
  awayTeamId: '',
  homeName: '',
  awayName: '',
};

export default function PredictionScreen() {
  const { baseUrl, setBaseUrl, loaded } = useApiBaseUrl();
  const [baseUrlDraft, setBaseUrlDraft] = useState(baseUrl);
  const [showSettings, setShowSettings] = useState(false);

  const [bulletin, setBulletin] = useState<BulletinResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [showMatchForm, setShowMatchForm] = useState(false);
  const [matchForm, setMatchForm] = useState(EMPTY_MATCH_FORM);
  const [matchLoading, setMatchLoading] = useState(false);
  const [matchError, setMatchError] = useState<string | null>(null);
  const [matchResult, setMatchResult] = useState<BulletinResponse | null>(null);

  const { isPremium, purchase } = useSubscription();
  const { remaining, limit, limitReached, recordUsage } = useDailyQueryLimit();
  const [showPaywall, setShowPaywall] = useState(false);

  useEffect(() => {
    setBaseUrlDraft(baseUrl);
  }, [baseUrl]);

  const loadDemo = useCallback(
    async (isRefresh = false) => {
      if (!loaded) return;
      isRefresh ? setRefreshing(true) : setLoading(true);
      setError(null);
      try {
        const data = await fetchBulletinDemo(baseUrl);
        setBulletin(data);
      } catch (err) {
        setBulletin(null);
        setError(err instanceof ApiError ? err.message : 'Bilinmeyen bir hata oluştu.');
      } finally {
        isRefresh ? setRefreshing(false) : setLoading(false);
      }
    },
    [baseUrl, loaded]
  );

  useEffect(() => {
    loadDemo();
  }, [loadDemo]);

  const handleSaveBaseUrl = () => {
    setBaseUrl(baseUrlDraft);
    setShowSettings(false);
  };

  const handleMatchSubmit = async () => {
    const { homeTeamId, awayTeamId, homeName, awayName } = matchForm;
    if (!homeTeamId.trim() || !awayTeamId.trim() || !homeName.trim() || !awayName.trim()) {
      setMatchError('Tüm alanları doldurun.');
      return;
    }
    if (!isPremium && limitReached) {
      setShowPaywall(true);
      return;
    }
    setMatchLoading(true);
    setMatchError(null);
    setMatchResult(null);
    try {
      const data = await fetchMatch(baseUrl, {
        homeTeamId: homeTeamId.trim(),
        awayTeamId: awayTeamId.trim(),
        homeName: homeName.trim(),
        awayName: awayName.trim(),
      });
      setMatchResult(data);
      if (!isPremium) recordUsage();
    } catch (err) {
      setMatchError(err instanceof ApiError ? err.message : 'Bilinmeyen bir hata oluştu.');
    } finally {
      setMatchLoading(false);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      contentContainerStyle={styles.content}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => loadDemo(true)} tintColor="#8fa3c0" />}
    >
      <View style={styles.headerRow}>
        <Text style={styles.title}>Futbol Analiz Motoru</Text>
        <Pressable onPress={() => setShowSettings((prev) => !prev)} hitSlop={10}>
          <Text style={styles.settingsToggle}>⚙️</Text>
        </Pressable>
      </View>

      <View style={styles.planRow}>
        {isPremium ? (
          <Text style={styles.planBadgePremium}>⭐ Premium</Text>
        ) : (
          <>
            <Text style={styles.planBadgeFree}>
              Ücretsiz plan: bugün {remaining}/{limit} gerçek maç sorgusu kaldı
            </Text>
            <Pressable onPress={() => setShowPaywall(true)} hitSlop={8}>
              <Text style={styles.upgradeLink}>Yükselt</Text>
            </Pressable>
          </>
        )}
      </View>

      {showSettings && (
        <View style={styles.settingsBox}>
          <Text style={styles.settingsLabel}>API Adresi</Text>
          <TextInput
            style={styles.input}
            value={baseUrlDraft}
            onChangeText={setBaseUrlDraft}
            placeholder="http://192.168.1.23:8000"
            placeholderTextColor="#5a6472"
            autoCapitalize="none"
            autoCorrect={false}
          />
          <Pressable style={styles.saveButton} onPress={handleSaveBaseUrl}>
            <Text style={styles.saveButtonText}>Kaydet ve Yenile</Text>
          </Pressable>
        </View>
      )}

      {loading && <ActivityIndicator color="#3d8bfd" style={styles.loadingIndicator} />}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>{error}</Text>
          <Pressable onPress={() => loadDemo()} style={styles.retryButton}>
            <Text style={styles.retryButtonText}>Tekrar Dene</Text>
          </Pressable>
        </View>
      )}

      {bulletin && (
        <>
          {bulletin.demo_warning && (
            <View style={styles.demoBanner}>
              <Text style={styles.demoBannerText}>⚠️ {bulletin.demo_warning}</Text>
            </View>
          )}
          <View style={styles.riskBanner}>
            <Text style={styles.riskBannerText}>{bulletin.risk_warning}</Text>
          </View>

          {bulletin.matches.map((match) => (
            <MatchCard key={`${match.home.id}-${match.away.id}`} match={match} />
          ))}
        </>
      )}

      <Pressable
        style={styles.sectionToggle}
        onPress={() => setShowMatchForm((prev) => !prev)}
      >
        <Text style={styles.sectionToggleText}>
          {showMatchForm ? '▲ Gerçek Maç Sorgula' : '▼ Gerçek Maç Sorgula'}
        </Text>
      </Pressable>

      {showMatchForm && (
        <View style={styles.formBox}>
          <Text style={styles.formHint}>
            Takım ID'lerini bulmak için sunucudaki /teams uç noktasını kullanın (ör.
            /teams?competition=PL). Gerçek tahmin için sunucuda football-data.org (ve
            isteğe bağlı API-Football, The Odds API) anahtarlarının tanımlı olması gerekir.
          </Text>
          <TextInput
            style={styles.input}
            placeholder="Ev sahibi takım ID"
            placeholderTextColor="#5a6472"
            value={matchForm.homeTeamId}
            onChangeText={(v) => setMatchForm((f) => ({ ...f, homeTeamId: v }))}
            autoCapitalize="none"
          />
          <TextInput
            style={styles.input}
            placeholder="Ev sahibi takım adı"
            placeholderTextColor="#5a6472"
            value={matchForm.homeName}
            onChangeText={(v) => setMatchForm((f) => ({ ...f, homeName: v }))}
          />
          <TextInput
            style={styles.input}
            placeholder="Deplasman takım ID"
            placeholderTextColor="#5a6472"
            value={matchForm.awayTeamId}
            onChangeText={(v) => setMatchForm((f) => ({ ...f, awayTeamId: v }))}
            autoCapitalize="none"
          />
          <TextInput
            style={styles.input}
            placeholder="Deplasman takım adı"
            placeholderTextColor="#5a6472"
            value={matchForm.awayName}
            onChangeText={(v) => setMatchForm((f) => ({ ...f, awayName: v }))}
          />
          <Pressable style={styles.saveButton} onPress={handleMatchSubmit} disabled={matchLoading}>
            <Text style={styles.saveButtonText}>{matchLoading ? 'Sorgulanıyor…' : 'Tahmin Al'}</Text>
          </Pressable>

          {matchLoading && <ActivityIndicator color="#3d8bfd" style={styles.loadingIndicator} />}

          {matchError && (
            <View style={styles.errorBox}>
              <Text style={styles.errorText}>{matchError}</Text>
            </View>
          )}

          {matchResult?.matches.map((match) => (
            <MatchCard
              key={`${match.home.id}-${match.away.id}`}
              match={match}
              restricted={!isPremium}
              onUpgradePress={() => setShowPaywall(true)}
            />
          ))}
        </View>
      )}

      <PaywallScreen
        visible={showPaywall}
        onClose={() => setShowPaywall(false)}
        onPurchase={async () => {
          await purchase();
          setShowPaywall(false);
        }}
      />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b1220',
  },
  content: {
    paddingTop: 64,
    paddingHorizontal: 20,
    paddingBottom: 40,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: '#ffffff',
  },
  settingsToggle: {
    fontSize: 20,
  },
  planRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  planBadgePremium: {
    color: '#f0c14b',
    fontSize: 13,
    fontWeight: '700',
  },
  planBadgeFree: {
    color: '#8fa3c0',
    fontSize: 12,
    flex: 1,
    marginRight: 8,
  },
  upgradeLink: {
    color: '#3d8bfd',
    fontSize: 12,
    fontWeight: '700',
  },
  settingsBox: {
    backgroundColor: '#141d2e',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  settingsLabel: {
    color: '#8fa3c0',
    fontSize: 12,
    marginBottom: 6,
  },
  input: {
    backgroundColor: '#0b1220',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#22304a',
    color: '#ffffff',
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 10,
    fontSize: 14,
  },
  saveButton: {
    backgroundColor: '#2e7d32',
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
  },
  saveButtonText: {
    color: '#ffffff',
    fontWeight: '700',
    fontSize: 13,
  },
  loadingIndicator: {
    marginVertical: 16,
  },
  errorBox: {
    backgroundColor: '#2a1414',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  errorText: {
    color: '#f0a3a3',
    fontSize: 13,
    marginBottom: 8,
  },
  retryButton: {
    alignSelf: 'flex-start',
  },
  retryButtonText: {
    color: '#3d8bfd',
    fontSize: 13,
    fontWeight: '700',
  },
  demoBanner: {
    backgroundColor: '#2a1f14',
    borderRadius: 10,
    padding: 12,
    marginBottom: 12,
  },
  demoBannerText: {
    color: '#f0b357',
    fontSize: 12,
    lineHeight: 17,
  },
  riskBanner: {
    backgroundColor: '#141d2e',
    borderRadius: 10,
    padding: 12,
    marginBottom: 16,
  },
  riskBannerText: {
    color: '#8fa3c0',
    fontSize: 11,
    lineHeight: 16,
  },
  sectionToggle: {
    marginTop: 8,
    marginBottom: 12,
  },
  sectionToggleText: {
    color: '#3d8bfd',
    fontSize: 14,
    fontWeight: '700',
  },
  formBox: {
    backgroundColor: '#141d2e',
    borderRadius: 10,
    padding: 12,
  },
  formHint: {
    color: '#8fa3c0',
    fontSize: 11,
    lineHeight: 16,
    marginBottom: 10,
  },
});
