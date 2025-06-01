import { StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useState } from 'react';
import { MaterialIcons, Ionicons } from '@expo/vector-icons';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

export default function ScannerScreen() {
  const [isScanning, setIsScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);

  const handleScan = () => {
    setIsScanning(true);
    // Симуляция сканирования
    setTimeout(() => {
      setIsScanning(false);
      setScanResult({
        name: 'Витамин D3 2000 IU',
        brand: 'Now Foods',
        ingredients: ['Витамин D3', 'Микрокристаллическая целлюлоза', 'Стеарат магния'],
        dosage: '1 капсула в день',
        warnings: ['Не превышать рекомендуемую дозу', 'Хранить в недоступном для детей месте'],
        confidence: 95
      });
    }, 2000);
  };

  const handleAddToStack = () => {
    Alert.alert('Успешно!', 'Добавка добавлена в ваш персональный стек');
    setScanResult(null);
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedView style={styles.header}>
        <ThemedText type="title">AI Сканирование</ThemedText>
        <ThemedText style={styles.subtitle}>
          Наведите камеру на этикетку добавки для анализа
        </ThemedText>
      </ThemedView>

      <ThemedView style={styles.scanArea}>
        {!scanResult ? (
          <ThemedView style={styles.cameraContainer}>
            <ThemedView style={styles.cameraFrame}>
              {isScanning ? (
                <ThemedView style={styles.scanningIndicator}>
                  <MaterialIcons name="camera-alt" size={80} color="#FF9800" />
                  <ThemedText style={styles.scanningText}>Сканирование...</ThemedText>
                </ThemedView>
              ) : (
                <TouchableOpacity style={styles.scanButton} onPress={handleScan}>
                  <MaterialIcons name="camera-alt" size={60} color="#fff" />
                  <ThemedText style={styles.scanButtonText}>Начать сканирование</ThemedText>
                </TouchableOpacity>
              )}
            </ThemedView>
            <ThemedView style={styles.instructions}>
              <ThemedText style={styles.instructionText}>
                • Убедитесь, что этикетка хорошо освещена
              </ThemedText>
              <ThemedText style={styles.instructionText}>
                • Держите камеру на расстоянии 10-15 см
              </ThemedText>
              <ThemedText style={styles.instructionText}>
                • Дождитесь автоматического распознавания
              </ThemedText>
            </ThemedView>
          </ThemedView>
        ) : (
          <ThemedView style={styles.resultContainer}>
            <ThemedView style={styles.resultHeader}>
              <Ionicons name="checkmark-circle" size={24} color="#4CAF50" />
              <ThemedText type="subtitle">Результат сканирования</ThemedText>
              <ThemedText style={styles.confidence}>Точность: {scanResult.confidence}%</ThemedText>
            </ThemedView>
            
            <ThemedView style={styles.resultCard}>
              <ThemedText type="subtitle">{scanResult.name}</ThemedText>
              <ThemedText style={styles.brand}>{scanResult.brand}</ThemedText>
              
              <ThemedView style={styles.section}>
                <ThemedText style={styles.sectionTitle}>Состав:</ThemedText>
                {scanResult.ingredients.map((ingredient: string, index: number) => (
                  <ThemedText key={index} style={styles.ingredient}>• {ingredient}</ThemedText>
                ))}
              </ThemedView>
              
              <ThemedView style={styles.section}>
                <ThemedText style={styles.sectionTitle}>Дозировка:</ThemedText>
                <ThemedText style={styles.dosage}>{scanResult.dosage}</ThemedText>
              </ThemedView>
              
              <ThemedView style={styles.section}>
                <ThemedText style={styles.sectionTitle}>Предупреждения:</ThemedText>
                {scanResult.warnings.map((warning: string, index: number) => (
                  <ThemedText key={index} style={styles.warning}>⚠️ {warning}</ThemedText>
                ))}
              </ThemedView>
            </ThemedView>
            
            <ThemedView style={styles.actions}>
              <TouchableOpacity style={styles.addButton} onPress={handleAddToStack}>
                <Ionicons name="add-circle" size={20} color="#fff" />
                <ThemedText style={styles.addButtonText}>Добавить в стек</ThemedText>
              </TouchableOpacity>
              <TouchableOpacity style={styles.rescanButton} onPress={() => setScanResult(null)}>
                <MaterialIcons name="camera-alt" size={20} color="#2196F3" />
                <ThemedText style={styles.rescanButtonText}>Сканировать еще</ThemedText>
              </TouchableOpacity>
            </ThemedView>
          </ThemedView>
        )}
      </ThemedView>
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
  scanArea: {
    flex: 1,
  },
  cameraContainer: {
    flex: 1,
  },
  cameraFrame: {
    flex: 1,
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderStyle: 'dashed',
    borderColor: '#ddd',
  },
  scanningIndicator: {
    alignItems: 'center',
  },
  scanningText: {
    marginTop: 16,
    fontSize: 18,
    color: '#FF9800',
  },
  scanButton: {
    alignItems: 'center',
    backgroundColor: '#FF9800',
    padding: 24,
    borderRadius: 16,
  },
  scanButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
  },
  instructions: {
    marginTop: 20,
    padding: 16,
    backgroundColor: '#e3f2fd',
    borderRadius: 8,
  },
  instructionText: {
    color: '#1976d2',
    marginBottom: 4,
  },
  resultContainer: {
    flex: 1,
  },
  resultHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 16,
  },
  confidence: {
    marginLeft: 'auto',
    color: '#4CAF50',
    fontWeight: '600',
  },
  resultCard: {
    backgroundColor: '#fff',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    marginBottom: 20,
  },
  brand: {
    color: '#666',
    fontSize: 14,
    marginBottom: 16,
  },
  section: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontWeight: '600',
    marginBottom: 8,
  },
  ingredient: {
    color: '#666',
    marginBottom: 2,
  },
  dosage: {
    color: '#666',
  },
  warning: {
    color: '#ff5722',
    marginBottom: 2,
  },
  actions: {
    flexDirection: 'row',
    gap: 12,
  },
  addButton: {
    flex: 1,
    backgroundColor: '#4CAF50',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  addButtonText: {
    color: '#fff',
    fontWeight: '600',
  },
  rescanButton: {
    flex: 1,
    backgroundColor: '#e3f2fd',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 12,
    borderRadius: 8,
    gap: 8,
  },
  rescanButtonText: {
    color: '#2196F3',
    fontWeight: '600',
  },
});