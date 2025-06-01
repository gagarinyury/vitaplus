import { StyleSheet, ScrollView, TouchableOpacity, Dimensions } from 'react-native';
import { useState } from 'react';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

const { width } = Dimensions.get('window');

interface StatCard {
  title: string;
  value: string;
  change: string;
  trend: 'up' | 'down' | 'stable';
  icon: string;
  color: string;
}

const mockStats: StatCard[] = [
  {
    title: 'Активных добавок',
    value: '8',
    change: '+2 за неделю',
    trend: 'up',
    icon: 'medical',
    color: '#4CAF50'
  },
  {
    title: 'Соблюдение режима',
    value: '85%',
    change: '+5% за месяц',
    trend: 'up',
    icon: 'checkmark-circle',
    color: '#2196F3'
  },
  {
    title: 'Заканчиваются',
    value: '3',
    change: 'Требуют заказа',
    trend: 'down',
    icon: 'warning',
    color: '#FF9800'
  },
  {
    title: 'Потрачено в месяц',
    value: '₽4,200',
    change: '-₽300 от плана',
    trend: 'down',
    icon: 'card',
    color: '#9C27B0'
  }
];

const mockWeeklyData = [
  { day: 'Пн', taken: 7, planned: 8 },
  { day: 'Вт', taken: 8, planned: 8 },
  { day: 'Ср', taken: 6, planned: 8 },
  { day: 'Чт', taken: 8, planned: 8 },
  { day: 'Пт', taken: 7, planned: 8 },
  { day: 'Сб', taken: 5, planned: 8 },
  { day: 'Вс', taken: 6, planned: 8 },
];

const mockCategories = [
  { name: 'Витамины', count: 4, percentage: 50, color: '#4CAF50' },
  { name: 'Минералы', count: 2, percentage: 25, color: '#2196F3' },
  { name: 'Жирные кислоты', count: 1, percentage: 12.5, color: '#FF9800' },
  { name: 'Аминокислоты', count: 1, percentage: 12.5, color: '#9C27B0' },
];

export default function InsightsScreen() {
  const [timeRange, setTimeRange] = useState<'week' | 'month' | 'year'>('week');

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up': return 'trending-up';
      case 'down': return 'trending-down';
      default: return 'remove';
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up': return '#4CAF50';
      case 'down': return '#F44336';
      default: return '#666';
    }
  };

  const renderStatCard = (stat: StatCard, index: number) => (
    <ThemedView key={index} style={styles.statCard}>
      <ThemedView style={styles.statHeader}>
        <Ionicons name={stat.icon as any} size={24} color={stat.color} />
        <ThemedText style={styles.statValue}>{stat.value}</ThemedText>
      </ThemedView>
      <ThemedText style={styles.statTitle}>{stat.title}</ThemedText>
      <ThemedView style={styles.statChange}>
        <Ionicons 
          name={getTrendIcon(stat.trend)} 
          size={14} 
          color={getTrendColor(stat.trend)} 
        />
        <ThemedText style={[styles.changeText, { color: getTrendColor(stat.trend) }]}>
          {stat.change}
        </ThemedText>
      </ThemedView>
    </ThemedView>
  );

  const renderWeeklyChart = () => (
    <ThemedView style={styles.chartContainer}>
      <ThemedText style={styles.chartTitle}>Соблюдение режима</ThemedText>
      <ThemedView style={styles.chart}>
        {mockWeeklyData.map((day, index) => {
          const percentage = (day.taken / day.planned) * 100;
          const height = (percentage / 100) * 80;
          return (
            <ThemedView key={index} style={styles.chartBar}>
              <ThemedView style={styles.barContainer}>
                <ThemedView 
                  style={[
                    styles.bar, 
                    { 
                      height: height,
                      backgroundColor: percentage === 100 ? '#4CAF50' : percentage >= 75 ? '#FF9800' : '#F44336'
                    }
                  ]} 
                />
              </ThemedView>
              <ThemedText style={styles.barLabel}>{day.day}</ThemedText>
              <ThemedText style={styles.barValue}>{day.taken}/{day.planned}</ThemedText>
            </ThemedView>
          );
        })}
      </ThemedView>
    </ThemedView>
  );

  const renderCategoryChart = () => (
    <ThemedView style={styles.categoryContainer}>
      <ThemedText style={styles.chartTitle}>Распределение по категориям</ThemedText>
      <ThemedView style={styles.categories}>
        {mockCategories.map((category, index) => (
          <ThemedView key={index} style={styles.categoryItem}>
            <ThemedView style={styles.categoryHeader}>
              <ThemedView 
                style={[styles.categoryDot, { backgroundColor: category.color }]} 
              />
              <ThemedText style={styles.categoryName}>{category.name}</ThemedText>
              <ThemedText style={styles.categoryCount}>{category.count}</ThemedText>
            </ThemedView>
            <ThemedView style={styles.categoryBar}>
              <ThemedView 
                style={[
                  styles.categoryProgress, 
                  { 
                    width: `${category.percentage}%`,
                    backgroundColor: category.color 
                  }
                ]} 
              />
            </ThemedView>
          </ThemedView>
        ))}
      </ThemedView>
    </ThemedView>
  );

  return (
    <ThemedView style={styles.container}>
      <ThemedView style={styles.header}>
        <ThemedText type="title">Инсайты</ThemedText>
        <ThemedText style={styles.subtitle}>
          Статистика и аналитика приема добавок
        </ThemedText>
      </ThemedView>

      <ThemedView style={styles.timeRangeContainer}>
        {(['week', 'month', 'year'] as const).map((range) => (
          <TouchableOpacity
            key={range}
            style={[styles.timeRangeButton, timeRange === range && styles.activeTimeRange]}
            onPress={() => setTimeRange(range)}
          >
            <ThemedText 
              style={[styles.timeRangeText, timeRange === range && styles.activeTimeRangeText]}
            >
              {range === 'week' ? 'Неделя' : range === 'month' ? 'Месяц' : 'Год'}
            </ThemedText>
          </TouchableOpacity>
        ))}
      </ThemedView>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <ThemedView style={styles.statsGrid}>
          {mockStats.map((stat, index) => renderStatCard(stat, index))}
        </ThemedView>

        {renderWeeklyChart()}
        {renderCategoryChart()}

        <ThemedView style={styles.achievementsContainer}>
          <ThemedText style={styles.chartTitle}>Достижения</ThemedText>
          <ThemedView style={styles.achievement}>
            <Ionicons name="trophy" size={24} color="#FFD700" />
            <ThemedView style={styles.achievementText}>
              <ThemedText style={styles.achievementTitle}>7 дней подряд!</ThemedText>
              <ThemedText style={styles.achievementDesc}>Принимали все добавки по расписанию</ThemedText>
            </ThemedView>
          </ThemedView>
          <ThemedView style={styles.achievement}>
            <Ionicons name="star" size={24} color="#4CAF50" />
            <ThemedView style={styles.achievementText}>
              <ThemedText style={styles.achievementTitle}>Месяц здоровья</ThemedText>
              <ThemedText style={styles.achievementDesc}>Соблюдение режима более 80%</ThemedText>
            </ThemedView>
          </ThemedView>
        </ThemedView>

        <ThemedView style={styles.exportContainer}>
          <TouchableOpacity style={styles.exportButton}>
            <MaterialIcons name="file-download" size={20} color="#2196F3" />
            <ThemedText style={styles.exportButtonText}>Экспорт отчета</ThemedText>
          </TouchableOpacity>
          <TouchableOpacity style={styles.shareButton}>
            <Ionicons name="share" size={20} color="#fff" />
            <ThemedText style={styles.shareButtonText}>Поделиться</ThemedText>
          </TouchableOpacity>
        </ThemedView>
      </ScrollView>
    </ThemedView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  header: {
    marginBottom: 20,
  },
  subtitle: {
    color: '#666',
    marginTop: 8,
  },
  timeRangeContainer: {
    flexDirection: 'row',
    marginBottom: 20,
    backgroundColor: '#f5f5f5',
    borderRadius: 8,
    padding: 4,
  },
  timeRangeButton: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  activeTimeRange: {
    backgroundColor: '#607D8B',
  },
  timeRangeText: {
    color: '#666',
    fontSize: 14,
  },
  activeTimeRangeText: {
    color: '#fff',
    fontWeight: '600',
  },
  content: {
    flex: 1,
  },
  statsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    width: (width - 44) / 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  statHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
  },
  statTitle: {
    color: '#666',
    fontSize: 12,
    marginBottom: 4,
  },
  statChange: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  changeText: {
    fontSize: 12,
  },
  chartContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 16,
  },
  chart: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-end',
    height: 120,
  },
  chartBar: {
    alignItems: 'center',
    flex: 1,
  },
  barContainer: {
    height: 80,
    justifyContent: 'flex-end',
    marginBottom: 8,
  },
  bar: {
    width: 20,
    borderRadius: 2,
  },
  barLabel: {
    fontSize: 12,
    color: '#666',
    marginBottom: 2,
  },
  barValue: {
    fontSize: 10,
    color: '#999',
  },
  categoryContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  categories: {
    gap: 12,
  },
  categoryItem: {
    gap: 8,
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  categoryDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
  },
  categoryName: {
    flex: 1,
    fontSize: 14,
  },
  categoryCount: {
    fontSize: 14,
    fontWeight: '600',
  },
  categoryBar: {
    height: 6,
    backgroundColor: '#f0f0f0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  categoryProgress: {
    height: '100%',
    borderRadius: 3,
  },
  achievementsContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  achievement: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#f0f0f0',
  },
  achievementText: {
    flex: 1,
  },
  achievementTitle: {
    fontWeight: '600',
    marginBottom: 2,
  },
  achievementDesc: {
    color: '#666',
    fontSize: 12,
  },
  exportContainer: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  exportButton: {
    flex: 1,
    backgroundColor: '#e3f2fd',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  exportButtonText: {
    color: '#2196F3',
    fontWeight: '600',
  },
  shareButton: {
    flex: 1,
    backgroundColor: '#607D8B',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  shareButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
});