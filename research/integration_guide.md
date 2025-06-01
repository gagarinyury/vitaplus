# 🔗 Руководство по интеграции API взаимодействий БАДов

## 📦 Что создано

1. **База данных взаимодействий**: 1910 взаимодействий из 25 витаминов/минералов
2. **Python API сервер**: Flask API для проверки взаимодействий
3. **HTML интерфейс**: Красивый веб-интерфейс для просмотра данных
4. **JSON/XML экспорт**: Структурированные данные для разработки

## 🚀 Запуск API сервера

```bash
# Установка зависимостей
pip install flask flask-cors

# Запуск сервера
python3 interactions_api.py
```

API будет доступен по адресу: `http://localhost:5000`

## 📋 API Эндпоинты

### 1. Проверка работоспособности
```http
GET /api/health
```

**Ответ:**
```json
{
  "status": "ok",
  "total_interactions": 1910,
  "total_supplements": 25
}
```

### 2. Проверка взаимодействий между БАДами
```http
POST /api/check-interactions
Content-Type: application/json

{
  "supplements": ["Zinc", "Calcium", "Iron"]
}
```

**Ответ:**
```json
{
  "interactions_found": 15,
  "interactions": [
    {
      "supplement": "Zinc",
      "interacts_with": "Calcium",
      "interaction_type": "negative",
      "effect": "Calcium may reduce zinc absorption",
      "severity": "medium"
    }
  ],
  "warnings": [
    {
      "supplement": "Zinc",
      "warning": "High doses may interfere with copper absorption",
      "severity": "high"
    }
  ],
  "high_severity_count": 2
}
```

### 3. Информация о конкретном БАДе
```http
GET /api/supplement/Zinc
```

### 4. Поиск БАДов
```http
GET /api/search?q=vitam
```

### 5. Список всех БАДов
```http
GET /api/supplements
```

## 📱 Интеграция с React Native

### Установка в VitaPlus проекте:

```bash
npm install axios
```

### Пример компонента проверки взаимодействий:

```typescript
// components/InteractionChecker.tsx
import React, { useState } from 'react';
import { View, Text, Button, Alert } from 'react-native';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

interface InteractionResult {
  interactions_found: number;
  warnings: Array<{
    supplement: string;
    warning: string;
    severity: string;
  }>;
  high_severity_count: number;
}

export const InteractionChecker: React.FC = () => {
  const [supplements] = useState(['Zinc', 'Calcium', 'Iron']);
  const [result, setResult] = useState<InteractionResult | null>(null);

  const checkInteractions = async () => {
    try {
      const response = await axios.post(`${API_BASE}/check-interactions`, {
        supplements: supplements
      });
      
      setResult(response.data);
      
      if (response.data.high_severity_count > 0) {
        Alert.alert(
          '⚠️ Внимание!', 
          `Найдено ${response.data.high_severity_count} серьезных взаимодействий`
        );
      }
    } catch (error) {
      console.error('Ошибка проверки взаимодействий:', error);
    }
  };

  return (
    <View style={{ padding: 20 }}>
      <Text style={{ fontSize: 18, fontWeight: 'bold' }}>
        Проверка взаимодействий БАДов
      </Text>
      
      <Button title="Проверить взаимодействия" onPress={checkInteractions} />
      
      {result && (
        <View style={{ marginTop: 20 }}>
          <Text>Найдено взаимодействий: {result.interactions_found}</Text>
          <Text>Серьезных: {result.high_severity_count}</Text>
          
          {result.warnings.map((warning, index) => (
            <View key={index} style={{ 
              marginTop: 10, 
              padding: 10, 
              backgroundColor: warning.severity === 'high' ? '#ffebee' : '#fff3e0',
              borderRadius: 5 
            }}>
              <Text style={{ fontWeight: 'bold' }}>{warning.supplement}</Text>
              <Text>{warning.warning}</Text>
            </View>
          ))}
        </View>
      )}
    </View>
  );
};
```

### Хук для работы с API:

```typescript
// hooks/useInteractions.ts
import { useState, useCallback } from 'react';
import axios from 'axios';

const API_BASE = 'http://localhost:5000/api';

export const useInteractions = () => {
  const [loading, setLoading] = useState(false);

  const checkInteractions = useCallback(async (supplements: string[]) => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE}/check-interactions`, {
        supplements
      });
      return response.data;
    } catch (error) {
      console.error('Ошибка API:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const searchSupplements = useCallback(async (query: string) => {
    try {
      const response = await axios.get(`${API_BASE}/search`, {
        params: { q: query }
      });
      return response.data.matches;
    } catch (error) {
      console.error('Ошибка поиска:', error);
      return [];
    }
  }, []);

  return {
    checkInteractions,
    searchSupplements,
    loading
  };
};
```

## 🎯 Интеграция в экраны VitaPlus

### Scanner Screen (app/(tabs)/scanner.tsx)
Добавить проверку взаимодействий после сканирования штрихкода:

```typescript
import { useInteractions } from '../hooks/useInteractions';

const ScannerScreen = () => {
  const { checkInteractions } = useInteractions();
  
  const handleBarcodeScan = async (barcode: string) => {
    // Логика определения БАДа по штрихкоду
    const supplement = await getSupplementFromBarcode(barcode);
    
    // Получить текущие БАДы пользователя
    const currentSupplements = await getUserSupplements();
    
    // Проверить взаимодействия
    const interactions = await checkInteractions([
      ...currentSupplements,
      supplement
    ]);
    
    if (interactions.high_severity_count > 0) {
      // Показать предупреждение
      showInteractionWarning(interactions);
    }
  };
};
```

### Search Screen (app/(tabs)/search.tsx)
Добавить поиск БАДов с проверкой взаимодействий:

```typescript
const SearchScreen = () => {
  const { searchSupplements, checkInteractions } = useInteractions();
  
  const handleSupplementSearch = async (query: string) => {
    const matches = await searchSupplements(query);
    // Показать результаты поиска
  };
  
  const addToMySupplements = async (supplement: string) => {
    const currentSupplements = await getUserSupplements();
    const interactions = await checkInteractions([
      ...currentSupplements,
      supplement
    ]);
    
    // Предупредить о взаимодействиях перед добавлением
    if (interactions.interactions_found > 0) {
      showInteractionDialog(interactions, supplement);
    } else {
      addSupplementToUser(supplement);
    }
  };
};
```

## 🗄️ Хранение данных пользователя

Рекомендуется использовать AsyncStorage для хранения списка БАДов пользователя:

```typescript
import AsyncStorage from '@react-native-async-storage/async-storage';

export const UserSupplementsService = {
  async getSupplements(): Promise<string[]> {
    try {
      const supplements = await AsyncStorage.getItem('user_supplements');
      return supplements ? JSON.parse(supplements) : [];
    } catch (error) {
      console.error('Ошибка загрузки БАДов:', error);
      return [];
    }
  },

  async addSupplement(supplement: string): Promise<void> {
    try {
      const current = await this.getSupplements();
      const updated = [...current, supplement];
      await AsyncStorage.setItem('user_supplements', JSON.stringify(updated));
    } catch (error) {
      console.error('Ошибка сохранения БАДа:', error);
    }
  },

  async removeSupplement(supplement: string): Promise<void> {
    try {
      const current = await this.getSupplements();
      const updated = current.filter(s => s !== supplement);
      await AsyncStorage.setItem('user_supplements', JSON.stringify(updated));
    } catch (error) {
      console.error('Ошибка удаления БАДа:', error);
    }
  }
};
```

## 🎨 UI Компоненты

### Компонент предупреждения о взаимодействиях:

```typescript
interface InteractionWarningProps {
  interactions: InteractionResult;
  onClose: () => void;
}

export const InteractionWarning: React.FC<InteractionWarningProps> = ({
  interactions,
  onClose
}) => {
  return (
    <Modal visible={true} animationType="slide">
      <View style={styles.container}>
        <Text style={styles.title}>⚠️ Обнаружены взаимодействия</Text>
        
        {interactions.warnings.map((warning, index) => (
          <View key={index} style={[
            styles.warningCard,
            { backgroundColor: warning.severity === 'high' ? '#ffebee' : '#fff3e0' }
          ]}>
            <Text style={styles.supplementName}>{warning.supplement}</Text>
            <Text style={styles.warningText}>{warning.warning}</Text>
            <Text style={styles.severity}>Серьезность: {warning.severity}</Text>
          </View>
        ))}
        
        <Button title="Понятно" onPress={onClose} />
      </View>
    </Modal>
  );
};
```

## 🔄 Обновление базы данных

Для обновления базы взаимодействий:

1. Запустить `python3 parse_interactions.py` для пересоздания базы
2. Перезапустить API сервер
3. Проверить новые данные через `/api/health`

## 📱 Deployment для продакшена

### Docker контейнер для API:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "interactions_api.py"]
```

### Heroku deployment:
```bash
# Создать Procfile
echo "web: python interactions_api.py" > Procfile

# Deployment
heroku create vitaplus-interactions-api
git push heroku main
```

## 🎯 Следующие шаги

1. **Интеграция в главные экраны VitaPlus**
2. **Добавление пуш-уведомлений о взаимодействиях**
3. **Персонализация рекомендаций**
4. **Расширение базы данных через PubMed API**
5. **Добавление лекарственных взаимодействий**

---

💡 **Готово к интеграции!** База данных содержит 1910 взаимодействий и готова для использования в VitaPlus приложении.