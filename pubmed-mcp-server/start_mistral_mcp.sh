#!/bin/bash

echo "🚀 Запускаем Mistral + MCP Server..."
echo ""

# Активируем виртуальное окружение
source ~/mlx_env/bin/activate

# Переходим в директорию
cd "$(dirname "$0")"

# Проверяем что MCP сервер собран
if [ ! -f "dist/index.js" ]; then
    echo "📦 Собираем MCP сервер..."
    npm run build
fi

echo "✅ Все готово!"
echo ""
echo "🌐 Веб-интерфейс: http://localhost:5001"
echo "💬 Командная строка: python3 mistral_mcp_client.py 'ваш запрос'"
echo ""
echo "🔥 Выберите режим:"
echo "1) Веб-интерфейс (рекомендуется)"
echo "2) Командная строка"
echo ""

read -p "Введите номер (1 или 2): " choice

case $choice in
    1)
        echo "🌐 Запускаем веб-интерфейс..."
        python3 web_interface.py
        ;;
    2)
        echo "💬 Режим командной строки"
        read -p "🔍 Введите ваш запрос: " query
        python3 mistral_mcp_client.py "$query"
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac