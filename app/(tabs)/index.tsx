import { Image } from 'expo-image';
import { Platform, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons, MaterialIcons, Feather } from '@expo/vector-icons';
import { router } from 'expo-router';

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
      <TouchableOpacity 
        style={styles.featureCard} 
        onPress={() => router.push('/(tabs)/search')}
      >
        <ThemedView style={styles.featureRow}>
          <Ionicons name="search" size={20} color="#2196F3" />
          <ThemedText type="subtitle" style={styles.featureTitle}>Поиск БАДов</ThemedText>
          <Ionicons name="chevron-forward" size={18} color="#ccc" style={styles.chevron} />
        </ThemedView>
        <ThemedText style={styles.featureDescription}>
          База данных добавок с детальной информацией
        </ThemedText>
      </TouchableOpacity>
      <TouchableOpacity 
        style={styles.featureCard} 
        onPress={() => router.push('/(tabs)/scanner')}
      >
        <ThemedView style={styles.featureRow}>
          <MaterialIcons name="camera-alt" size={20} color="#FF9800" />
          <ThemedText type="subtitle" style={styles.featureTitle}>AI Сканирование</ThemedText>
          <Ionicons name="chevron-forward" size={18} color="#ccc" style={styles.chevron} />
        </ThemedView>
        <ThemedText style={styles.featureDescription}>
          Анализ этикеток через камеру
        </ThemedText>
      </TouchableOpacity>
      <TouchableOpacity 
        style={styles.featureCard} 
        onPress={() => router.push('/(tabs)/stack')}
      >
        <ThemedView style={styles.featureRow}>
          <Ionicons name="library" size={20} color="#9C27B0" />
          <ThemedText type="subtitle" style={styles.featureTitle}>Персональный стек</ThemedText>
          <Ionicons name="chevron-forward" size={18} color="#ccc" style={styles.chevron} />
        </ThemedView>
        <ThemedText style={styles.featureDescription}>
          Управление своими добавками
        </ThemedText>
      </TouchableOpacity>
      <TouchableOpacity 
        style={styles.featureCard} 
        onPress={() => router.push('/(tabs)/analysis')}
      >
        <ThemedView style={styles.featureRow}>
          <Feather name="zap" size={20} color="#F44336" />
          <ThemedText type="subtitle" style={styles.featureTitle}>AI Анализ</ThemedText>
          <Ionicons name="chevron-forward" size={18} color="#ccc" style={styles.chevron} />
        </ThemedView>
        <ThemedText style={styles.featureDescription}>
          Проверка совместимости и рекомендации
        </ThemedText>
      </TouchableOpacity>
      <TouchableOpacity 
        style={styles.featureCard} 
        onPress={() => router.push('/(tabs)/insights')}
      >
        <ThemedView style={styles.featureRow}>
          <Ionicons name="analytics" size={20} color="#607D8B" />
          <ThemedText type="subtitle" style={styles.featureTitle}>Инсайты</ThemedText>
          <Ionicons name="chevron-forward" size={18} color="#ccc" style={styles.chevron} />
        </ThemedView>
        <ThemedText style={styles.featureDescription}>
          Статистика и аналитика приема
        </ThemedText>
      </TouchableOpacity>
    </ParallaxScrollView>
  );
}

const styles = StyleSheet.create({
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  featureCard: {
    backgroundColor: '#fff',
    borderRadius: 8,
    padding: 10,
    marginBottom: 6,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.06,
    shadowRadius: 1,
    elevation: 1,
    gap: 4,
  },
  featureRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: -0.3,
  },
  featureDescription: {
    fontSize: 15,
    color: '#666',
    lineHeight: 20,
    letterSpacing: -0.2,
  },
  chevron: {
    marginLeft: 'auto',
  },
  reactLogo: {
    height: 140,
    width: 220,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
});
