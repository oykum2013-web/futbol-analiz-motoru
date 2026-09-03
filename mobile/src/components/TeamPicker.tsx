import { useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { ApiError, fetchTeams } from '../api/client';
import type { TeamListItem } from '../api/types';

const COMPETITIONS: { code: string; label: string }[] = [
  { code: 'PL', label: 'Premier League' },
  { code: 'BL1', label: 'Bundesliga' },
  { code: 'PD', label: 'La Liga' },
  { code: 'SA', label: 'Serie A' },
  { code: 'FL1', label: 'Ligue 1' },
];

type Selected = { id: string; name: string } | null;

type Props = {
  baseUrl: string;
  selectedHome: Selected;
  selectedAway: Selected;
  onSelectHome: (team: TeamListItem) => void;
  onSelectAway: (team: TeamListItem) => void;
};

function TeamChips({
  teams,
  selectedId,
  onSelect,
}: {
  teams: TeamListItem[];
  selectedId?: string;
  onSelect: (team: TeamListItem) => void;
}) {
  return (
    <View style={styles.chipWrap}>
      {teams.map((team) => {
        const active = String(team.id) === selectedId;
        return (
          <Pressable
            key={team.id}
            style={[styles.chip, active && styles.chipActive]}
            onPress={() => onSelect(team)}
          >
            <Text style={[styles.chipText, active && styles.chipTextActive]}>
              {team.short_name || team.name}
            </Text>
          </Pressable>
        );
      })}
    </View>
  );
}

export default function TeamPicker({ baseUrl, selectedHome, selectedAway, onSelectHome, onSelectAway }: Props) {
  const [competition, setCompetition] = useState('PL');
  const [teams, setTeams] = useState<TeamListItem[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadTeams = async () => {
    setLoading(true);
    setError(null);
    setTeams(null);
    try {
      const data = await fetchTeams(baseUrl, competition);
      setTeams(data.teams);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Bilinmeyen bir hata oluştu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View>
      <Text style={styles.label}>Lig</Text>
      <View style={styles.chipWrap}>
        {COMPETITIONS.map((c) => (
          <Pressable
            key={c.code}
            style={[styles.chip, competition === c.code && styles.chipActive]}
            onPress={() => setCompetition(c.code)}
          >
            <Text style={[styles.chipText, competition === c.code && styles.chipTextActive]}>
              {c.label}
            </Text>
          </Pressable>
        ))}
      </View>

      <Pressable style={styles.loadButton} onPress={loadTeams} disabled={loading}>
        <Text style={styles.loadButtonText}>{loading ? 'Yükleniyor…' : 'Takımları Getir'}</Text>
      </Pressable>

      {loading && <ActivityIndicator color="#3d8bfd" style={styles.spinner} />}

      {error && <Text style={styles.errorText}>{error}</Text>}

      {teams && (
        <>
          <Text style={styles.label}>Ev Sahibi</Text>
          <TeamChips teams={teams} selectedId={selectedHome?.id} onSelect={onSelectHome} />

          <Text style={styles.label}>Deplasman</Text>
          <TeamChips teams={teams} selectedId={selectedAway?.id} onSelect={onSelectAway} />
        </>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  label: {
    color: '#8fa3c0',
    fontSize: 12,
    marginTop: 10,
    marginBottom: 6,
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  chip: {
    backgroundColor: '#0b1220',
    borderWidth: 1,
    borderColor: '#22304a',
    borderRadius: 16,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 6,
    marginBottom: 6,
  },
  chipActive: {
    backgroundColor: '#3d8bfd',
    borderColor: '#3d8bfd',
  },
  chipText: {
    color: '#d3ddeb',
    fontSize: 12,
  },
  chipTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  loadButton: {
    alignSelf: 'flex-start',
    backgroundColor: '#22304a',
    borderRadius: 8,
    paddingHorizontal: 14,
    paddingVertical: 8,
    marginTop: 4,
  },
  loadButtonText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '700',
  },
  spinner: {
    marginTop: 10,
  },
  errorText: {
    color: '#f0a3a3',
    fontSize: 12,
    marginTop: 8,
  },
});
