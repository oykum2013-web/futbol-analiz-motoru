import { StyleSheet, Text, View } from 'react-native';
import type { BulletinMatchItem } from '../api/types';

type Props = {
  match: BulletinMatchItem;
};

const CONFIDENCE_COLORS: Record<string, string> = {
  Yüksek: '#2e7d32',
  Orta: '#c77b1a',
  Düşük: '#b3401f',
  'Çok Düşük': '#8a1f1f',
  'Yetersiz Veri': '#5a6472',
};

function confidenceColor(confidence: string): string {
  return CONFIDENCE_COLORS[confidence] ?? '#5a6472';
}

function ProbabilityBar({ label, percent }: { label: string; percent: number }) {
  return (
    <View style={styles.probRow}>
      <Text style={styles.probLabel}>{label}</Text>
      <View style={styles.probTrack}>
        <View style={[styles.probFill, { width: `${Math.max(0, Math.min(100, percent))}%` }]} />
      </View>
      <Text style={styles.probValue}>%{percent.toFixed(1)}</Text>
    </View>
  );
}

export default function MatchCard({ match }: Props) {
  const { prediction, data_gaps: dataGaps } = match;
  const badgeColor = confidenceColor(prediction.confidence);

  return (
    <View style={styles.card}>
      <Text style={styles.teams}>
        {prediction.home.name} <Text style={styles.vs}>vs</Text> {prediction.away.name}
      </Text>

      <View style={styles.probs}>
        <ProbabilityBar label="Ev Sahibi" percent={prediction.home_win_prob} />
        <ProbabilityBar label="Beraberlik" percent={prediction.draw_prob} />
        <ProbabilityBar label="Deplasman" percent={prediction.away_win_prob} />
      </View>

      <View style={[styles.confidenceBadge, { backgroundColor: badgeColor }]}>
        <Text style={styles.confidenceText}>Güven: {prediction.confidence}</Text>
      </View>

      {dataGaps.length > 0 && (
        <View style={styles.gapsBox}>
          <Text style={styles.gapsTitle}>⚠️ Eksik veri</Text>
          {dataGaps.map((gap) => (
            <Text key={gap} style={styles.gapsText}>
              • {gap}
            </Text>
          ))}
        </View>
      )}

      {prediction.rationale.length > 0 && (
        <View style={styles.rationaleBox}>
          {prediction.rationale.map((line) => (
            <Text key={line} style={styles.rationaleText}>
              • {line}
            </Text>
          ))}
        </View>
      )}

      <Text style={styles.disclaimer}>{prediction.disclaimer}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#141d2e',
    borderRadius: 14,
    padding: 16,
    marginBottom: 14,
  },
  teams: {
    color: '#ffffff',
    fontSize: 17,
    fontWeight: '700',
    marginBottom: 12,
  },
  vs: {
    color: '#8fa3c0',
    fontWeight: '400',
  },
  probs: {
    marginBottom: 12,
  },
  probRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 6,
  },
  probLabel: {
    width: 78,
    color: '#d3ddeb',
    fontSize: 12,
  },
  probTrack: {
    flex: 1,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#22304a',
    overflow: 'hidden',
    marginHorizontal: 8,
  },
  probFill: {
    height: '100%',
    backgroundColor: '#3d8bfd',
    borderRadius: 4,
  },
  probValue: {
    width: 52,
    textAlign: 'right',
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  confidenceBadge: {
    alignSelf: 'flex-start',
    borderRadius: 8,
    paddingHorizontal: 10,
    paddingVertical: 4,
    marginBottom: 10,
  },
  confidenceText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  gapsBox: {
    backgroundColor: '#2a1f14',
    borderRadius: 8,
    padding: 10,
    marginBottom: 10,
  },
  gapsTitle: {
    color: '#f0b357',
    fontSize: 12,
    fontWeight: '700',
    marginBottom: 4,
  },
  gapsText: {
    color: '#e3c396',
    fontSize: 12,
    lineHeight: 17,
  },
  rationaleBox: {
    marginBottom: 10,
  },
  rationaleText: {
    color: '#8fa3c0',
    fontSize: 12,
    lineHeight: 17,
  },
  disclaimer: {
    color: '#5a6472',
    fontSize: 11,
    fontStyle: 'italic',
  },
});
