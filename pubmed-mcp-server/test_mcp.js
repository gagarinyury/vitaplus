// Простой тест MCP сервера
const { searchPubmed } = require('./dist/tools/search-pubmed.js');

async function test() {
    try {
        console.log("🧪 Тестируем MCP сервер...");
        
        const result = await searchPubmed({
            query: "magnesium safety",
            max_results: 3
        });
        
        console.log("✅ Результат:", JSON.stringify(result, null, 2));
    } catch (error) {
        console.error("❌ Ошибка:", error.message);
    }
}

test();