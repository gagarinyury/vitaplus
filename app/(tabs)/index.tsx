import { Image } from 'expo-image';
import { Platform, StyleSheet } from 'react-native';
import { Ionicons, MaterialIcons, Feather } from '@expo/vector-icons';

import { HelloWave } from '@/components/HelloWave';
import ParallaxScrollView from '@/components/ParallaxScrollView';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export default function HomeScreen() {
  return (
    <ParallaxScrollView
      headerBackgroundColor={{ light: '#A1CEDC', dark: '#1D3D47' }}
      headerImage={
        <Image
          source={require('@/assets/images/partial-react-logo.png')}
          style={styles.reactLogo}
        />
      }>
      <ThemedView style={styles.titleContainer}>
        <ThemedText type="title">VitaPlus</ThemedText>
        <Ionicons name="nutrition" size={32} color="#4CAF50" />
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedView style={styles.featureRow}>
          <Ionicons name="search" size={24} color="#2196F3" />
          <ThemedText type="subtitle">Поиск БАДов</ThemedText>
        </ThemedView>
        <ThemedText>
          База данных добавок с детальной информацией
        </ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedView style={styles.featureRow}>
          <MaterialIcons name="camera-alt" size={24} color="#FF9800" />
          <ThemedText type="subtitle">AI Сканирование</ThemedText>
        </ThemedView>
        <ThemedText>
          Анализ этикеток через камеру
        </ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedView style={styles.featureRow}>
          <Ionicons name="library" size={24} color="#9C27B0" />
          <ThemedText type="subtitle">Персональный стек</ThemedText>
        </ThemedView>
        <ThemedText>
          Управление своими добавками
        </ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedView style={styles.featureRow}>
          <Feather name="zap" size={24} color="#F44336" />
          <ThemedText type="subtitle">AI Анализ</ThemedText>
        </ThemedView>
        <ThemedText>
          Проверка совместимости и рекомендации
        </ThemedText>
      </ThemedView>
      <ThemedView style={styles.stepContainer}>
        <ThemedView style={styles.featureRow}>
          <Ionicons name="analytics" size={24} color="#607D8B" />
          <ThemedText type="subtitle">Инсайты</ThemedText>
        </ThemedView>
        <ThemedText>
          Статистика и аналитика приема
        </ThemedText>
      </ThemedView>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 8,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
});
