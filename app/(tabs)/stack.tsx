import { StyleSheet, FlatList, TouchableOpacity, Alert } from 'react-native';
import { useState } from 'react';
import { Ionicons, MaterialIcons } from '@expo/vector-icons';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

interface Supplement {
  id: string;
  name: string;
  dosage: string;
  frequency: string;
  timeOfDay: string;
  remaining: number;
  totalSupply: number;
  category: string;
  isActive: boolean;
}

const mockStack: Supplement[] = [
  {
    id: '1',
    name: 'Витамин D3',
    dosage: '2000 IU',
    frequency: 'Ежедневно',
    timeOfDay: 'Утром',
    remaining: 45,
    totalSupply: 60,
    category: 'Витамины',
    isActive: true,
  },
  {
    id: '2',
    name: 'Омега-3',
    dosage: '1000 мг',
    frequency: 'Ежедневно',
    timeOfDay: 'С едой',
    remaining: 20,
    totalSupply: 90,
    category: 'Жирные кислоты',
    isActive: true,
  },
  {
    id: '3',
    name: 'Магний',
    dosage: '400 мг',
    frequency: 'Вечером',
    timeOfDay: 'Перед сном',
    remaining: 5,
    totalSupply: 30,
    category: 'Минералы',
    isActive: false,
  },
];

export default function StackScreen() {
  const [supplements, setSupplements] = useState(mockStack);
  const [filter, setFilter] = useState<'all' | 'active' | 'low'>('all');

  const toggleSupplementStatus = (id: string) => {
    setSupplements(prev => 
      prev.map(item => 
        item.id === id ? { ...item, isActive: !item.isActive } : item
      )
    );
  };

  const deleteSuplement = (id: string) => {
    Alert.alert(
      'Удалить добавку?',
      'Вы уверены, что хотите удалить эту добавку из стека?',
      [
        { text: 'Отмена', style: 'cancel' },
        { 
          text: 'Удалить', 
          style: 'destructive',
          onPress: () => setSupplements(prev => prev.filter(item => item.id !== id))
        },
      ]
    );
  };

  const getFilteredSupplements = () => {
    switch (filter) {
      case 'active':
        return supplements.filter(item => item.isActive);
      case 'low':
        return supplements.filter(item => item.remaining / item.totalSupply <= 0.2);
      default:
        return supplements;
    }
  };

  const getProgressColor = (remaining: number, total: number) => {
    const percentage = remaining / total;
    if (percentage <= 0.2) return '#f44336';
    if (percentage <= 0.5) return '#ff9800';
    return '#4caf50';
  };

  const renderSupplement = ({ item }: { item: Supplement }) => (
    <ThemedView style={styles.supplementCard}>
      <ThemedView style={styles.cardHeader}>
        <ThemedView style={styles.titleRow}>
          <ThemedText type="subtitle">{item.name}</ThemedText>
          <TouchableOpacity onPress={() => toggleSupplementStatus(item.id)}>
            <Ionicons 
              name={item.isActive ? "pause-circle" : "play-circle"} 
              size={24} 
              color={item.isActive ? "#ff9800" : "#4caf50"} 
            />
          </TouchableOpacity>
        </ThemedView>
        <ThemedView style={styles.statusRow}>
          <ThemedText style={[styles.status, { color: item.isActive ? '#4caf50' : '#666' }]}>
            {item.isActive ? 'Активно' : 'Приостановлено'}
          </ThemedText>
          <ThemedText style={styles.category}>{item.category}</ThemedText>
        </ThemedView>
      </ThemedView>

      <ThemedView style={styles.dosageInfo}>
        <ThemedView style={styles.dosageRow}>
          <Ionicons name="medical" size={16} color="#666" />
          <ThemedText style={styles.dosageText}>{item.dosage} • {item.frequency}</ThemedText>
        </ThemedView>
        <ThemedView style={styles.dosageRow}>
          <Ionicons name="time" size={16} color="#666" />
          <ThemedText style={styles.dosageText}>{item.timeOfDay}</ThemedText>
        </ThemedView>
      </ThemedView>

      <ThemedView style={styles.progressSection}>
        <ThemedView style={styles.progressHeader}>
          <ThemedText style={styles.progressText}>
            Осталось: {item.remaining} из {item.totalSupply}
          </ThemedText>
          <ThemedText style={[styles.progressPercent, { color: getProgressColor(item.remaining, item.totalSupply) }]}>
            {Math.round((item.remaining / item.totalSupply) * 100)}%
          </ThemedText>
        </ThemedView>
        <ThemedView style={styles.progressBar}>
          <ThemedView 
            style={[
              styles.progressFill, 
              { 
                width: `${(item.remaining / item.totalSupply) * 100}%`,
                backgroundColor: getProgressColor(item.remaining, item.totalSupply)
              }
            ]} 
          />
        </ThemedView>
      </ThemedView>

      <ThemedView style={styles.actions}>
        <TouchableOpacity style={styles.editButton}>
          <MaterialIcons name="edit" size={16} color="#2196F3" />
          <ThemedText style={styles.editText}>Редактировать</ThemedText>
        </TouchableOpacity>
        <TouchableOpacity style={styles.deleteButton} onPress={() => deleteSuplement(item.id)}>
          <MaterialIcons name="delete" size={16} color="#f44336" />
          <ThemedText style={styles.deleteText}>Удалить</ThemedText>
        </TouchableOpacity>
      </ThemedView>
    </ThemedView>
  );

  return (
    <ThemedView style={styles.container}>
      <ThemedView style={styles.header}>
        <ThemedText type="title">Мой стек</ThemedText>
        <ThemedText style={styles.subtitle}>
          Управление персональными добавками
        </ThemedText>
      </ThemedView>

      <ThemedView style={styles.filterContainer}>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'all' && styles.activeFilter]}
          onPress={() => setFilter('all')}
        >
          <ThemedText style={[styles.filterText, filter === 'all' && styles.activeFilterText]}>
            Все ({supplements.length})
          </ThemedText>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'active' && styles.activeFilter]}
          onPress={() => setFilter('active')}
        >
          <ThemedText style={[styles.filterText, filter === 'active' && styles.activeFilterText]}>
            Активные ({supplements.filter(item => item.isActive).length})
          </ThemedText>
        </TouchableOpacity>
        <TouchableOpacity 
          style={[styles.filterButton, filter === 'low' && styles.activeFilter]}
          onPress={() => setFilter('low')}
        >
          <ThemedText style={[styles.filterText, filter === 'low' && styles.activeFilterText]}>
            Заканчиваются ({supplements.filter(item => item.remaining / item.totalSupply <= 0.2).length})
          </ThemedText>
        </TouchableOpacity>
      </ThemedView>

      <FlatList
        data={getFilteredSupplements()}
        renderItem={renderSupplement}
        keyExtractor={item => item.id}
        style={styles.list}
        showsVerticalScrollIndicator={false}
        ListEmptyComponent={
          <ThemedView style={styles.emptyContainer}>
            <Ionicons name="library-outline" size={64} color="#ccc" />
            <ThemedText style={styles.emptyText}>Стек пуст</ThemedText>
            <ThemedText style={styles.emptySubtext}>
              Добавьте добавки через поиск или сканирование
            </ThemedText>
          </ThemedView>
        }
      />

      <TouchableOpacity style={styles.fab}>
        <Ionicons name="add" size={24} color="#fff" />
      </TouchableOpacity>
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
  filterContainer: {
    flexDirection: 'row',
    marginBottom: 16,
    gap: 8,
  },
  filterButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f5f5f5',
  },
  activeFilter: {
    backgroundColor: '#9C27B0',
  },
  filterText: {
    fontSize: 12,
    color: '#666',
  },
  activeFilterText: {
    color: '#fff',
  },
  list: {
    flex: 1,
  },
  supplementCard: {
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
  cardHeader: {
    marginBottom: 12,
  },
  titleRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  statusRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  status: {
    fontSize: 12,
    fontWeight: '600',
  },
  category: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  dosageInfo: {
    marginBottom: 12,
    gap: 4,
  },
  dosageRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  dosageText: {
    color: '#666',
    fontSize: 14,
  },
  progressSection: {
    marginBottom: 12,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  progressText: {
    fontSize: 14,
    color: '#666',
  },
  progressPercent: {
    fontSize: 14,
    fontWeight: '600',
  },
  progressBar: {
    height: 6,
    backgroundColor: '#f0f0f0',
    borderRadius: 3,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 3,
  },
  actions: {
    flexDirection: 'row',
    gap: 16,
  },
  editButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  editText: {
    color: '#2196F3',
    fontSize: 14,
  },
  deleteButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  deleteText: {
    color: '#f44336',
    fontSize: 14,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingTop: 60,
  },
  emptyText: {
    fontSize: 18,
    color: '#ccc',
    marginTop: 16,
  },
  emptySubtext: {
    color: '#ccc',
    textAlign: 'center',
    marginTop: 8,
  },
  fab: {
    position: 'absolute',
    bottom: 20,
    right: 20,
    width: 56,
    height: 56,
    backgroundColor: '#9C27B0',
    borderRadius: 28,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
});