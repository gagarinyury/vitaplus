import { StyleSheet, TextInput, FlatList, TouchableOpacity, Alert } from 'react-native';
import { useState } from 'react';
import { Ionicons, Feather } from '@expo/vector-icons';
import { router } from 'expo-router';
import { ThemedText } from '@/components/ThemedText';
import { ThemedView } from '@/components/ThemedView';

const mockSupplements = [
  { id: '1', name: 'Витамин D3', category: 'Витамины', description: 'Поддержка иммунитета и костей' },
  { id: '2', name: 'Омега-3', category: 'Жирные кислоты', description: 'Здоровье сердца и мозга' },
  { id: '3', name: 'Магний', category: 'Минералы', description: 'Расслабление мышц и нервной системы' },
  { id: '4', name: 'Цинк', category: 'Минералы', description: 'Иммунитет и заживление ран' },
  { id: '5', name: 'Витамин B12', category: 'Витамины', description: 'Энергия и нервная система' },
];

export default function SearchScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filteredSupplements, setFilteredSupplements] = useState(mockSupplements);
  const [selectedSupplements, setSelectedSupplements] = useState<typeof mockSupplements>([]);

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    const filtered = mockSupplements.filter(item =>
      item.name.toLowerCase().includes(query.toLowerCase()) ||
      item.category.toLowerCase().includes(query.toLowerCase())
    );
    setFilteredSupplements(filtered);
  };

  const handleAddSupplement = (supplement: typeof mockSupplements[0]) => {
    if (selectedSupplements.find(item => item.id === supplement.id)) {
      Alert.alert('Уже добавлено', 'Эта добавка уже в списке для анализа');
      return;
    }
    setSelectedSupplements(prev => [...prev, supplement]);
  };

  const handleRemoveSupplement = (supplementId: string) => {
    setSelectedSupplements(prev => prev.filter(item => item.id !== supplementId));
  };

  const handleAnalyze = () => {
    if (selectedSupplements.length === 0) {
      Alert.alert('Нет добавок', 'Добавьте хотя бы одну добавку для анализа');
      return;
    }
    router.push('/(tabs)/analysis');
  };

  const renderSupplement = ({ item }: { item: typeof mockSupplements[0] }) => {
    const isSelected = selectedSupplements.find(selected => selected.id === item.id);
    
    return (
      <TouchableOpacity style={styles.supplementCard}>
        <ThemedView style={styles.cardHeader}>
          <ThemedText type="subtitle">{item.name}</ThemedText>
          <ThemedText style={styles.category}>{item.category}</ThemedText>
        </ThemedView>
        <ThemedText style={styles.description}>{item.description}</ThemedText>
        <TouchableOpacity 
          style={[styles.addButton, isSelected && styles.addedButton]} 
          onPress={() => handleAddSupplement(item)}
          disabled={!!isSelected}
        >
          <Ionicons 
            name={isSelected ? "checkmark-circle" : "add-circle"} 
            size={24} 
            color={isSelected ? "#666" : "#4CAF50"} 
          />
          <ThemedText style={[styles.addText, isSelected && styles.addedText]}>
            {isSelected ? "Добавлено" : "Добавить"}
          </ThemedText>
        </TouchableOpacity>
      </TouchableOpacity>
    );
  };

  return (
    <ThemedView style={styles.container}>
      <ThemedView style={styles.header}>
        <ThemedText type="title">Поиск БАДов</ThemedText>
        <ThemedView style={styles.searchContainer}>
          <Ionicons name="search" size={20} color="#666" style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder="Найти добавку..."
            value={searchQuery}
            onChangeText={handleSearch}
          />
        </ThemedView>
      </ThemedView>
      
      <FlatList
        data={filteredSupplements}
        renderItem={renderSupplement}
        keyExtractor={item => item.id}
        style={[styles.list, selectedSupplements.length > 0 && styles.listWithSelected]}
        showsVerticalScrollIndicator={false}
      />

      {selectedSupplements.length > 0 && (
        <ThemedView style={styles.selectedContainer}>
          <ThemedView style={styles.selectedHeader}>
            <ThemedText style={styles.selectedTitle}>
              Для анализа ({selectedSupplements.length})
            </ThemedText>
            <TouchableOpacity onPress={() => setSelectedSupplements([])}>
              <ThemedText style={styles.clearText}>Очистить</ThemedText>
            </TouchableOpacity>
          </ThemedView>
          
          <FlatList
            data={selectedSupplements}
            horizontal
            renderItem={({ item }) => (
              <ThemedView style={styles.selectedItem}>
                <ThemedText style={styles.selectedItemName}>{item.name}</ThemedText>
                <TouchableOpacity onPress={() => handleRemoveSupplement(item.id)}>
                  <Ionicons name="close-circle" size={16} color="#f44336" />
                </TouchableOpacity>
              </ThemedView>
            )}
            keyExtractor={item => item.id}
            showsHorizontalScrollIndicator={false}
            style={styles.selectedList}
          />
          
          <TouchableOpacity style={styles.analyzeButton} onPress={handleAnalyze}>
            <Feather name="zap" size={20} color="#fff" />
            <ThemedText style={styles.analyzeButtonText}>Анализировать</ThemedText>
          </TouchableOpacity>
        </ThemedView>
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
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 12,
    paddingHorizontal: 12,
    marginTop: 16,
  },
  searchIcon: {
    marginRight: 8,
  },
  searchInput: {
    flex: 1,
    height: 44,
    fontSize: 16,
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  category: {
    fontSize: 12,
    color: '#666',
    backgroundColor: '#e3f2fd',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  description: {
    color: '#666',
    marginBottom: 12,
  },
  addButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  addText: {
    color: '#4CAF50',
    fontWeight: '600',
  },
  addedButton: {
    opacity: 0.6,
  },
  addedText: {
    color: '#666',
  },
  listWithSelected: {
    marginBottom: 180,
  },
  selectedContainer: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    backgroundColor: '#fff',
    borderTopWidth: 1,
    borderTopColor: '#e0e0e0',
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  selectedHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  selectedTitle: {
    fontSize: 16,
    fontWeight: '600',
  },
  clearText: {
    color: '#f44336',
    fontSize: 14,
  },
  selectedList: {
    marginBottom: 16,
  },
  selectedItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
    borderRadius: 20,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginRight: 8,
    gap: 6,
  },
  selectedItemName: {
    fontSize: 14,
    color: '#333',
  },
  analyzeButton: {
    backgroundColor: '#F44336',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 14,
    borderRadius: 8,
    gap: 8,
  },
  analyzeButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});