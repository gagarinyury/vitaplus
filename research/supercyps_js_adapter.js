/**
 * SuperCYPsPred API - JavaScript/TypeScript адаптация
 * Портирование Python API для использования в React Native / Node.js
 */

class SuperCYPsPredAPI {
    constructor() {
        // API ЭНДПОИНТЫ
        this.enqueueUrl = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_enqueue_new.php";
        this.retrieveUrl = "http://insilico-cyp.charite.de/SuperCYPsPred/src/api_retrieve.php";
        
        // НАСТРОЙКИ
        this.defaultWaitTime = 10000; // 10 секунд в миллисекундах
        this.maxRetries = 60;
        this.requestTimeout = 30000; // 30 секунд
        
        // ДОСТУПНЫЕ МОДЕЛИ
        this.availableModels = ['CYP1A2', 'CYP2C9', 'CYP2C19', 'CYP2D6', 'CYP3A4', 'ALL_MODELS'];
        this.inputTypes = ['name', 'smiles'];
    }

    /**
     * ШАГ 1: Отправка запроса на обработку
     * @param {string} inputData - Название БАДа или SMILES строка
     * @param {string} inputType - 'name' или 'smiles'
     * @param {string} models - CYP модели или 'ALL_MODELS'
     * @returns {Promise<string|null>} ID задачи или null при ошибке
     */
    async enqueueRequest(inputData, inputType = 'name', models = 'ALL_MODELS') {
        console.log('📤 Отправка POST запроса:');
        console.log(`   URL: ${this.enqueueUrl}`);
        console.log(`   Данные: ${JSON.stringify({inputData, inputType, models})}`);

        try {
            // Подготовка FormData для POST запроса
            const formData = new FormData();
            formData.append('input', inputData);
            formData.append('input_type', inputType);
            formData.append('models', models);

            // HTTP POST запрос
            const response = await fetch(this.enqueueUrl, {
                method: 'POST',
                body: formData,
                // НЕ добавляем Content-Type - браузер сам установит для FormData
            });

            console.log('📨 Ответ сервера:');
            console.log(`   Статус код: ${response.status}`);
            console.log(`   Заголовки:`, Object.fromEntries(response.headers.entries()));

            // ОБРАБОТКА СТАТУС КОДОВ
            switch (response.status) {
                case 200:
                    // Успешная отправка
                    const taskId = await response.text();
                    console.log(`   ID задачи: ${taskId.trim()}`);
                    return taskId.trim();

                case 429:
                    // Слишком много запросов
                    console.warn('⚠️ Слишком много запросов (429)');
                    const retryAfter = response.headers.get('Retry-After') || this.defaultWaitTime / 1000;
                    console.log(`   Повтор через: ${retryAfter} секунд`);
                    throw new Error(`Too many requests. Retry after ${retryAfter} seconds`);

                case 403:
                    // Превышена дневная квота
                    console.error('❌ Превышена дневная квота (403)');
                    throw new Error('Daily quota exceeded');

                default:
                    const errorText = await response.text();
                    console.error(`❌ Неожиданный статус код: ${response.status}`);
                    console.error(`   Ответ: ${errorText}`);
                    throw new Error(`Unexpected status code: ${response.status}`);
            }

        } catch (error) {
            if (error.message.includes('fetch')) {
                console.error('❌ Ошибка сети:', error.message);
                throw new Error('Network error during request submission');
            }
            throw error;
        }
    }

    /**
     * ШАГ 2: Получение результатов по ID задачи
     * @param {string} taskId - ID задачи
     * @returns {Promise<string|null>} CSV содержимое или null при ошибке
     */
    async retrieveResults(taskId) {
        console.log(`📥 Получение результатов для задачи: ${taskId}`);

        for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
            try {
                console.log(`🔄 Попытка ${attempt}/${this.maxRetries}`);

                // Подготовка данных для проверки статуса
                const formData = new FormData();
                formData.append('task_id', taskId);

                const response = await fetch(this.retrieveUrl, {
                    method: 'POST',
                    body: formData,
                });

                console.log(`   Статус код: ${response.status}`);

                switch (response.status) {
                    case 200:
                        // Результаты готовы!
                        const csvUrl = await response.text();
                        console.log(`✅ Результаты готовы: ${csvUrl.trim()}`);
                        return await this.downloadCSVResults(csvUrl.trim());

                    case 404:
                        // Вычисления еще не завершены
                        console.log('⏳ Вычисления не завершены (404)');
                        const retryAfter = parseInt(response.headers.get('Retry-After')) || (this.defaultWaitTime / 1000);
                        console.log(`   Ожидание: ${retryAfter} секунд`);
                        
                        await this.sleep(retryAfter * 1000);
                        continue;

                    case 429:
                        // Слишком много запросов
                        console.warn('⚠️ Слишком много запросов (429)');
                        const waitTime = parseInt(response.headers.get('Retry-After')) || (this.defaultWaitTime / 1000);
                        await this.sleep(waitTime * 1000);
                        continue;

                    default:
                        const errorText = await response.text();
                        console.error(`❌ Неожиданный статус код: ${response.status}`);
                        console.error(`   Ответ: ${errorText}`);
                        throw new Error(`Unexpected status code: ${response.status}`);
                }

            } catch (error) {
                console.error(`❌ Ошибка при получении результатов (попытка ${attempt}):`, error.message);
                
                if (attempt === this.maxRetries) {
                    throw new Error('Max retries exceeded');
                }
                
                await this.sleep(this.defaultWaitTime);
            }
        }

        throw new Error('Превышено максимальное количество попыток');
    }

    /**
     * ШАГ 3: Скачивание CSV файла с результатами
     * @param {string} csvUrl - URL к CSV файлу
     * @returns {Promise<string>} CSV содержимое
     */
    async downloadCSVResults(csvUrl) {
        console.log(`📊 Скачивание CSV: ${csvUrl}`);

        try {
            const response = await fetch(csvUrl);

            if (response.ok) {
                const csvContent = await response.text();
                console.log('✅ CSV файл успешно скачан');
                console.log(`   Размер: ${csvContent.length} символов`);

                // Парсинг CSV для анализа
                const lines = csvContent.trim().split('\n');
                console.log(`   Строк данных: ${lines.length}`);

                if (lines.length > 0) {
                    console.log(`   Заголовки: ${lines[0]}`);
                    if (lines.length > 1) {
                        console.log(`   Первая строка данных: ${lines[1]}`);
                    }
                }

                return csvContent;
            } else {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

        } catch (error) {
            console.error('❌ Ошибка скачивания CSV:', error.message);
            throw new Error(`Failed to download CSV: ${error.message}`);
        }
    }

    /**
     * ПАРСИНГ CSV результатов в JavaScript объект
     * @param {string} csvContent - CSV содержимое
     * @returns {Object} Объект с предсказаниями CYP
     */
    parseCSVResults(csvContent) {
        const lines = csvContent.trim().split('\n');
        if (lines.length < 2) {
            throw new Error('Invalid CSV format');
        }

        const headers = lines[0].split(',').map(h => h.trim());
        const dataLine = lines[1].split(',').map(d => d.trim());

        const result = {
            compound: dataLine[0] || 'Unknown',
            predictions: {},
            metadata: {
                timestamp: new Date().toISOString(),
                source: 'SuperCYPsPred'
            }
        };

        // Извлечение предсказаний для каждого CYP фермента
        for (let i = 1; i < headers.length; i++) {
            const cypName = headers[i];
            const prediction = parseFloat(dataLine[i]);
            
            if (!isNaN(prediction)) {
                result.predictions[cypName] = {
                    value: prediction,
                    riskLevel: this.calculateRiskLevel(prediction),
                    interpretation: this.interpretPrediction(cypName, prediction)
                };
            }
        }

        return result;
    }

    /**
     * РАСЧЕТ УРОВНЯ РИСКА
     * @param {number} prediction - Значение предсказания (0-1)
     * @returns {string} Уровень риска
     */
    calculateRiskLevel(prediction) {
        if (prediction >= 0.7) return 'high';
        if (prediction >= 0.4) return 'medium';
        return 'low';
    }

    /**
     * ИНТЕРПРЕТАЦИЯ ПРЕДСКАЗАНИЯ
     * @param {string} cypName - Название CYP фермента
     * @param {number} prediction - Значение предсказания
     * @returns {string} Интерпретация
     */
    interpretPrediction(cypName, prediction) {
        const riskLevel = this.calculateRiskLevel(prediction);
        
        const interpretations = {
            high: `Высокая вероятность ингибирования ${cypName}. Возможны серьезные взаимодействия с лекарствами.`,
            medium: `Умеренная вероятность ингибирования ${cypName}. Возможны взаимодействия с некоторыми лекарствами.`,
            low: `Низкая вероятность ингибирования ${cypName}. Минимальный риск взаимодействий.`
        };

        return interpretations[riskLevel];
    }

    /**
     * ПОЛНЫЙ ЦИКЛ: Предсказание CYP профиля
     * @param {string} compound - Название соединения или SMILES
     * @param {string} inputType - 'name' или 'smiles'
     * @param {string} models - CYP модели
     * @returns {Promise<Object>} Результат предсказания
     */
    async predictCYPProfile(compound, inputType = 'name', models = 'ALL_MODELS') {
        console.log('🧬 Начало предсказания CYP профиля');
        console.log(`   Соединение: ${compound}`);
        console.log(`   Тип входа: ${inputType}`);
        console.log(`   Модели: ${models}`);
        console.log('='.repeat(60));

        try {
            // Шаг 1: Отправка запроса
            const taskId = await this.enqueueRequest(compound, inputType, models);
            console.log('='.repeat(60));

            // Шаг 2: Получение результатов
            const csvResults = await this.retrieveResults(taskId);
            console.log('='.repeat(60));

            // Шаг 3: Парсинг результатов
            const parsedResults = this.parseCSVResults(csvResults);
            
            console.log('🎯 Предсказание завершено!');
            console.log('📊 Результаты:', JSON.stringify(parsedResults, null, 2));

            return parsedResults;

        } catch (error) {
            console.error('❌ Ошибка предсказания CYP профиля:', error.message);
            throw error;
        }
    }

    /**
     * УТИЛИТА: Задержка выполнения
     * @param {number} ms - Миллисекунды
     */
    sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}

// ТЕСТИРОВАНИЕ API (для Node.js)
async function testAPI() {
    const api = new SuperCYPsPredAPI();

    try {
        console.log('🧪 ТЕСТ 1: Поиск по названию БАДа');
        const result1 = await api.predictCYPProfile('Zinc', 'name');
        console.log('✅ Тест 1 успешен');
        
        console.log('\n' + '='.repeat(80) + '\n');
        
        console.log('🧪 ТЕСТ 2: SMILES аспирина');
        const aspirinSMILES = 'CC(=O)OC1=CC=CC=C1C(=O)O';
        const result2 = await api.predictCYPProfile(aspirinSMILES, 'smiles');
        console.log('✅ Тест 2 успешен');

    } catch (error) {
        console.error('❌ Тест неудачен:', error.message);
    }
}

// ЭКСПОРТ ДЛЯ React Native / Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SuperCYPsPredAPI;
}

// Для тестирования (раскомментировать):
// testAPI();

/**
 * ПРИМЕР ИСПОЛЬЗОВАНИЯ В REACT NATIVE:
 * 
 * import SuperCYPsPredAPI from './supercyps_js_adapter';
 * 
 * const checkSupplementCYP = async (supplementName) => {
 *   const api = new SuperCYPsPredAPI();
 *   
 *   try {
 *     const result = await api.predictCYPProfile(supplementName);
 *     
 *     // Проверка высокого риска
 *     const highRiskCYPs = Object.entries(result.predictions)
 *       .filter(([cyp, data]) => data.riskLevel === 'high')
 *       .map(([cyp, data]) => ({ cyp, ...data }));
 *     
 *     if (highRiskCYPs.length > 0) {
 *       Alert.alert(
 *         '⚠️ CYP Взаимодействие',
 *         `${supplementName} может влиять на метаболизм лекарств`
 *       );
 *     }
 *     
 *     return result;
 *   } catch (error) {
 *     console.error('CYP проверка неудачна:', error);
 *     return null;
 *   }
 * };
 */