import { StyleSheet, TouchableOpacity, ScrollView, Alert } from 'react-native';
import { useState } from 'react';
import { Feather, Ionicons, MaterialIcons } from '@expo/vector-icons';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

interface AnalysisResult {
  compatibility: 'good' | 'warning' | 'danger';
  score: number;
  interactions: string[];
  recommendations: string[];
  deficiencies: string[];
  overdoses: string[];
}

const mockAnalysis: AnalysisResult = {
  compatibility: 'warning',
  score: 7.5,
  interactions: [
    'Кальций может снижать усвоение цинка при одновременном приеме',
    'Витамин D улучшает усвоение кальция'
  ],
  recommendations: [
    'Принимайте цинк за 2 часа до или после кальция',
    'Добавьте витамин K2 для лучшего усвоения кальция',
    'Рассмотрите добавление магния для баланса с кальцием'
  ],
  deficiencies: [
    'Недостаток омега-3 жирных кислот',
    'Низкий уровень витамина B12'
  ],
  overdoses: [
    'Превышение рекомендуемой дозы витамина A'
  ]
};

export default function AnalysisScreen() {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);

  const handleStartAnalysis = () => {
    setIsAnalyzing(true);
    // Симуляция анализа
    setTimeout(() => {
      setIsAnalyzing(false);
      setAnalysisResult(mockAnalysis);
    }, 3000);
  };

  const getCompatibilityColor = (compatibility: string) => {
    switch (compatibility) {
      case 'good': return '#4CAF50';
      case 'warning': return '#FF9800';
      case 'danger': return '#F44336';
      default: return '#666';
    }
  };

  const getCompatibilityIcon = (compatibility: string) => {
    switch (compatibility) {
      case 'good': return 'checkmark-circle';
      case 'warning': return 'warning';
      case 'danger': return 'close-circle';
      default: return 'help-circle';
    }
  };

  const getCompatibilityText = (compatibility: string) => {
    switch (compatibility) {
      case 'good': return 'Отличная совместимость';
      case 'warning': return 'Требует внимания';
      case 'danger': return 'Есть противопоказания';
      default: return 'Неизвестно';
    }
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedView style={styles.header}>
        <ThemedText type="title">AI Анализ</ThemedText>
        <ThemedText style={styles.subtitle}>
          Проверка совместимости добавок и персональные рекомендации
        </ThemedText>
      </ThemedView>

      {!analysisResult ? (
        <ThemedView style={styles.analysisContainer}>
          <ThemedView style={styles.analysisArea}>
            {isAnalyzing ? (
              <ThemedView style={styles.analyzingContainer}>
                <Feather name="zap" size={80} color="#F44336" />
                <ThemedText style={styles.analyzingText}>Анализируем ваш стек...</ThemedText>
                <ThemedText style={styles.analyzingSubtext}>
                  Проверяем взаимодействия и совместимость
                </ThemedText>
              </ThemedView>
            ) : (
              <ThemedView style={styles.startContainer}>
                <Feather name="zap" size={60} color="#F44336" />
                <ThemedText style={styles.startTitle}>Готовы к анализу?</ThemedText>
                <ThemedText style={styles.startDescription}>
                  ИИ проанализирует ваш текущий стек добавок и даст персональные рекомендации
                </ThemedText>
                <TouchableOpacity style={styles.analyzeButton} onPress={handleStartAnalysis}>
                  <Feather name="zap" size={20} color="#fff" />
                  <ThemedText style={styles.analyzeButtonText}>Начать анализ</ThemedText>
                </TouchableOpacity>
              </ThemedView>
            )}
          </ThemedView>

          <ThemedView style={styles.featuresContainer}>
            <ThemedText style={styles.featuresTitle}>Что анализирует ИИ:</ThemedText>
            <ThemedView style={styles.feature}>
              <Ionicons name="shield-checkmark" size={20} color="#4CAF50" />
              <ThemedText style={styles.featureText}>Взаимодействия между добавками</ThemedText>
            </ThemedView>
            <ThemedView style={styles.feature}>
              <Ionicons name="time" size={20} color="#2196F3" />
              <ThemedText style={styles.featureText}>Оптимальное время приема</ThemedText>
            </ThemedView>
            <ThemedView style={styles.feature}>
              <Ionicons name="analytics" size={20} color="#FF9800" />
              <ThemedText style={styles.featureText}>Дефициты и превышения</ThemedText>
            </ThemedView>
            <ThemedView style={styles.feature}>
              <Ionicons name="bulb" size={20} color="#9C27B0" />
              <ThemedText style={styles.featureText}>Персональные рекомендации</ThemedText>
            </ThemedView>
          </ThemedView>
        </ThemedView>
      ) : (
        <ScrollView style={styles.resultsContainer} showsVerticalScrollIndicator={false}>
          <ThemedView style={styles.scoreCard}>
            <ThemedView style={styles.scoreHeader}>
              <Ionicons 
                name={getCompatibilityIcon(analysisResult.compatibility)} 
                size={32} 
                color={getCompatibilityColor(analysisResult.compatibility)} 
              />
              <ThemedView style={styles.scoreInfo}>
                <ThemedText type="subtitle">{getCompatibilityText(analysisResult.compatibility)}</ThemedText>
                <ThemedText style={styles.scoreValue}>Оценка: {analysisResult.score}/10</ThemedText>
              </ThemedView>
            </ThemedView>
          </ThemedView>

          {analysisResult.interactions.length > 0 && (
            <ThemedView style={styles.section}>
              <ThemedView style={styles.sectionHeader}>
                <MaterialIcons name="swap-horiz" size={20} color="#FF9800" />
                <ThemedText style={styles.sectionTitle}>Взаимодействия</ThemedText>
              </ThemedView>
              {analysisResult.interactions.map((interaction, index) => (
                <ThemedView key={index} style={styles.listItem}>
                  <Ionicons name="information-circle" size={16} color="#FF9800" />
                  <ThemedText style={styles.listText}>{interaction}</ThemedText>
                </ThemedView>
              ))}
            </ThemedView>
          )}

          {analysisResult.deficiencies.length > 0 && (
            <ThemedView style={styles.section}>
              <ThemedView style={styles.sectionHeader}>
                <Ionicons name="trending-down" size={20} color="#F44336" />
                <ThemedText style={styles.sectionTitle}>Возможные дефициты</ThemedText>
              </ThemedView>
              {analysisResult.deficiencies.map((deficiency, index) => (
                <ThemedView key={index} style={styles.listItem}>
                  <Ionicons name="alert-circle" size={16} color="#F44336" />
                  <ThemedText style={styles.listText}>{deficiency}</ThemedText>
                </ThemedView>
              ))}
            </ThemedView>
          )}

          {analysisResult.overdoses.length > 0 && (
            <ThemedView style={styles.section}>
              <ThemedView style={styles.sectionHeader}>
                <Ionicons name="trending-up" size={20} color="#F44336" />
                <ThemedText style={styles.sectionTitle}>Превышения</ThemedText>
              </ThemedView>
              {analysisResult.overdoses.map((overdose, index) => (
                <ThemedView key={index} style={styles.listItem}>
                  <Ionicons name="warning" size={16} color="#F44336" />
                  <ThemedText style={styles.listText}>{overdose}</ThemedText>
                </ThemedView>
              ))}
            </ThemedView>
          )}

          <ThemedView style={styles.section}>
            <ThemedView style={styles.sectionHeader}>
              <Ionicons name="bulb" size={20} color="#4CAF50" />
              <ThemedText style={styles.sectionTitle}>Рекомендации</ThemedText>
            </ThemedView>
            {analysisResult.recommendations.map((recommendation, index) => (
              <ThemedView key={index} style={styles.listItem}>
                <Ionicons name="checkmark-circle" size={16} color="#4CAF50" />
                <ThemedText style={styles.listText}>{recommendation}</ThemedText>
              </ThemedView>
            ))}
          </ThemedView>

          <ThemedView style={styles.actionButtons}>
            <TouchableOpacity style={styles.reanalyzeButton} onPress={() => setAnalysisResult(null)}>
              <Feather name="refresh-cw" size={20} color="#2196F3" />
              <ThemedText style={styles.reanalyzeText}>Новый анализ</ThemedText>
            </TouchableOpacity>
            <TouchableOpacity 
              style={styles.exportButton} 
              onPress={() => Alert.alert('Экспорт', 'Отчет сохранен в галерею')}
            >
              <Ionicons name="download" size={20} color="#fff" />
              <ThemedText style={styles.exportText}>Экспорт отчета</ThemedText>
            </TouchableOpacity>
          </ThemedView>
        </ScrollView>
      )}
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
  analysisContainer: {
    flex: 1,
  },
  analysisArea: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    padding: 24,
    marginBottom: 20,
  },
  analyzingContainer: {
    alignItems: 'center',
  },
  analyzingText: {
    fontSize: 18,
    marginTop: 16,
    color: '#F44336',
  },
  analyzingSubtext: {
    color: '#666',
    textAlign: 'center',
    marginTop: 8,
  },
  startContainer: {
    alignItems: 'center',
  },
  startTitle: {
    fontSize: 20,
    fontWeight: '600',
    marginTop: 16,
    marginBottom: 8,
  },
  startDescription: {
    color: '#666',
    textAlign: 'center',
    marginBottom: 24,
  },
  analyzeButton: {
    backgroundColor: '#F44336',
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 8,
    gap: 8,
  },
  analyzeButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  featuresContainer: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
  },
  featuresTitle: {
    fontWeight: '600',
    marginBottom: 12,
  },
  feature: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  featureText: {
    color: '#666',
  },
  resultsContainer: {
    flex: 1,
  },
  scoreCard: {
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
  scoreHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  scoreInfo: {
    flex: 1,
  },
  scoreValue: {
    color: '#666',
    marginTop: 4,
  },
  section: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  sectionTitle: {
    fontWeight: '600',
  },
  listItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 8,
    marginBottom: 8,
  },
  listText: {
    flex: 1,
    color: '#666',
    lineHeight: 20,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
    marginBottom: 20,
  },
  reanalyzeButton: {
    flex: 1,
    backgroundColor: '#e3f2fd',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  reanalyzeText: {
    color: '#2196F3',
    fontWeight: '600',
  },
  exportButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  exportText: {
    color: '#fff',
    fontWeight: '600',
  },
});