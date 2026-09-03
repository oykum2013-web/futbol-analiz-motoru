import AsyncStorage from '@react-native-async-storage/async-storage';
import { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { StyleSheet, View } from 'react-native';
import { TOS_STORAGE_KEY } from './src/constants/legal';
import OnboardingScreen from './src/screens/OnboardingScreen';
import PredictionScreen from './src/screens/PredictionScreen';

export default function App() {
  const [tosAccepted, setTosAccepted] = useState<boolean | null>(null);

  useEffect(() => {
    AsyncStorage.getItem(TOS_STORAGE_KEY).then((value) => {
      setTosAccepted(value === 'true');
    });
  }, []);

  const handleAccept = () => {
    AsyncStorage.setItem(TOS_STORAGE_KEY, 'true');
    setTosAccepted(true);
  };

  if (tosAccepted === null) {
    return <View style={styles.loading} />;
  }

  return (
    <View style={styles.container}>
      {tosAccepted ? (
        <PredictionScreen />
      ) : (
        <OnboardingScreen onAccept={handleAccept} />
      )}
      <StatusBar style="light" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  loading: {
    flex: 1,
    backgroundColor: '#0b1220',
  },
});
