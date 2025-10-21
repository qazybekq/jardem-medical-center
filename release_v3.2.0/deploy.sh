#!/bin/bash

# 🚀 Скрипт для деплоя в Streamlit Cloud
# Автор: AI Assistant
# Дата: 2025-10-20

echo "🚀 ДЕПЛОЙ СИСТЕМЫ УПРАВЛЕНИЯ МЕДИЦИНСКИМ ЦЕНТРОМ"
echo "================================================"

# Проверяем, что мы в правильной директории
if [ ! -f "app.py" ]; then
    echo "❌ Ошибка: app.py не найден. Запусти скрипт из корневой папки проекта."
    exit 1
fi

# Проверяем, что Git инициализирован
if [ ! -d ".git" ]; then
    echo "📦 Инициализация Git репозитория..."
    git init
    echo "✅ Git репозиторий инициализирован"
fi

# Генерируем безопасные пароли
echo "🔐 Генерация безопасных паролей..."
python generate_secure_passwords.py

# Добавляем все файлы в Git
echo "📁 Добавление файлов в Git..."
git add .

# Проверяем статус
echo "📊 Статус Git репозитория:"
git status

# Создаем коммит
echo "💾 Создание коммита..."
git commit -m "Deploy: Medical Center Management System v3.2.0

- Полная система управления медицинским центром
- CRM система с календарем и приемами
- Аналитика и отчеты
- Справочники (клиенты, услуги, врачи)
- Система безопасности с ролями
- Резервное копирование
- Уведомления
- Готово к деплою в Streamlit Cloud"

echo "✅ Коммит создан"

# Проверяем, есть ли удаленный репозиторий
if ! git remote get-url origin > /dev/null 2>&1; then
    echo ""
    echo "🌐 НАСТРОЙКА GITHUB РЕПОЗИТОРИЯ"
    echo "================================"
    echo "1. Создай новый репозиторий на GitHub.com"
    echo "2. Скопируй URL репозитория"
    echo "3. Введи его ниже:"
    echo ""
    read -p "URL GitHub репозитория: " repo_url
    
    if [ -n "$repo_url" ]; then
        git remote add origin "$repo_url"
        echo "✅ Удаленный репозиторий добавлен"
    else
        echo "❌ URL не введен. Добавь репозиторий вручную:"
        echo "   git remote add origin https://github.com/USERNAME/REPO_NAME.git"
        exit 1
    fi
fi

# Переименовываем ветку в main
echo "🌿 Переименование ветки в main..."
git branch -M main

# Загружаем в GitHub
echo "⬆️  Загрузка в GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 УСПЕШНО ЗАГРУЖЕНО В GITHUB!"
    echo "==============================="
    echo ""
    echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
    echo "=================="
    echo ""
    echo "1. 🌐 Зайди на https://share.streamlit.io"
    echo "2. 🔑 Войди через GitHub аккаунт"
    echo "3. ➕ Нажми 'New app'"
    echo "4. ⚙️  Настрой приложение:"
    echo "   - Repository: твой_username/название_репозитория"
    echo "   - Branch: main"
    echo "   - Main file path: app.py"
    echo "5. 🔐 Добавь секреты (пароли из generated_passwords.txt)"
    echo "6. 🚀 Нажми 'Deploy!'"
    echo ""
    echo "📖 Подробная инструкция: DEPLOYMENT_GUIDE.md"
    echo ""
    echo "🎯 После деплоя твое приложение будет доступно по адресу:"
    echo "   https://название-приложения-твой-username.streamlit.app"
    echo ""
    echo "✅ Готово к деплою!"
else
    echo "❌ Ошибка при загрузке в GitHub"
    echo "Проверь настройки Git и права доступа"
    exit 1
fi
