import { useState } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
} from 'react-native';
import {
  DISCLAIMER_ACCEPT_LABEL,
  DISCLAIMER_CONTINUE_LABEL,
  DISCLAIMER_POINTS,
  DISCLAIMER_TITLE,
} from '../constants/legal';

type Props = {
  onAccept: () => void;
};

export default function OnboardingScreen({ onAccept }: Props) {
  const [checked, setChecked] = useState(false);

  return (
    <View style={styles.container}>
      <ScrollView
        style={styles.scroll}
        contentContainerStyle={styles.scrollContent}
      >
        <Text style={styles.title}>{DISCLAIMER_TITLE}</Text>
        {DISCLAIMER_POINTS.map((point) => (
          <View key={point} style={styles.pointRow}>
            <Text style={styles.bullet}>•</Text>
            <Text style={styles.pointText}>{point}</Text>
          </View>
        ))}
      </ScrollView>

      <Pressable
        style={styles.checkboxRow}
        onPress={() => setChecked((prev) => !prev)}
        accessibilityRole="checkbox"
        accessibilityState={{ checked }}
      >
        <View style={[styles.checkbox, checked && styles.checkboxChecked]}>
          {checked && <Text style={styles.checkboxMark}>✓</Text>}
        </View>
        <Text style={styles.checkboxLabel}>{DISCLAIMER_ACCEPT_LABEL}</Text>
      </Pressable>

      <Pressable
        style={[styles.continueButton, !checked && styles.continueButtonDisabled]}
        onPress={onAccept}
        disabled={!checked}
      >
        <Text style={styles.continueButtonText}>{DISCLAIMER_CONTINUE_LABEL}</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#0b1220',
    paddingTop: 64,
    paddingHorizontal: 20,
    paddingBottom: 24,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#ffffff',
    marginBottom: 16,
  },
  pointRow: {
    flexDirection: 'row',
    marginBottom: 12,
  },
  bullet: {
    color: '#8fa3c0',
    marginRight: 8,
    fontSize: 15,
  },
  pointText: {
    flex: 1,
    color: '#d3ddeb',
    fontSize: 14,
    lineHeight: 20,
  },
  checkboxRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 16,
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 5,
    borderWidth: 2,
    borderColor: '#8fa3c0',
    marginRight: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxChecked: {
    backgroundColor: '#2e7d32',
    borderColor: '#2e7d32',
  },
  checkboxMark: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  checkboxLabel: {
    flex: 1,
    color: '#d3ddeb',
    fontSize: 14,
  },
  continueButton: {
    backgroundColor: '#2e7d32',
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: 'center',
  },
  continueButtonDisabled: {
    backgroundColor: '#3a4759',
  },
  continueButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});
