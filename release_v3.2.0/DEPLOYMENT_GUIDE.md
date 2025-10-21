# 🚀 РУКОВОДСТВО ПО ДЕПЛОЮ В STREAMLIT CLOUD

**Дата:** 2025-10-20  
**Версия:** 3.2.0  
**Платформа:** Streamlit Cloud  

---

## 📋 ПРЕДВАРИТЕЛЬНЫЕ ТРЕБОВАНИЯ

### 1. GitHub аккаунт
- Создай аккаунт на [GitHub.com](https://github.com) если его нет
- Установи [Git](https://git-scm.com/) на компьютер

### 2. Streamlit Cloud аккаунт
- Зарегистрируйся на [share.streamlit.io](https://share.streamlit.io)
- Подключи GitHub аккаунт к Streamlit Cloud

---

## 🔧 ПОДГОТОВКА ПРОЕКТА

### Шаг 1: Создание .streamlit/config.toml

Создай файл конфигурации для Streamlit:

```toml
[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
```

### Шаг 2: Создание .streamlit/secrets.toml

Создай файл для секретов (пароли, API ключи):

```toml
# Пароли для пользователей
OWNER_PASSWORD = "твой_безопасный_пароль_владельца"
ADMIN_PASSWORD = "твой_безопасный_пароль_админа"
CRM_PASSWORD = "твой_безопасный_пароль_crm"

# Настройки базы данных (опционально)
DATABASE_URL = "sqlite:///medical_center.db"

# Настройки уведомлений (опционально)
EMAIL_SMTP_SERVER = "smtp.gmail.com"
EMAIL_SMTP_PORT = 587
EMAIL_USERNAME = "твой_email@gmail.com"
EMAIL_PASSWORD = "твой_пароль_приложения"
```

### Шаг 3: Обновление requirements.txt

Убедись, что в `requirements.txt` есть все необходимые зависимости:

```txt
streamlit>=1.28.0
pandas>=1.5.0
plotly>=5.15.0
bcrypt>=4.0.1
requests>=2.31.0
email-validator>=2.1.0
```

### Шаг 4: Создание .gitignore

Создай файл `.gitignore`:

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environment
venv/
env/
ENV/

# Database
*.db
*.sqlite
*.sqlite3

# Secrets
.streamlit/secrets.toml
.env

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log

# Backups
backups/
```

---

## 📤 ЗАГРУЗКА В GITHUB

### Шаг 1: Инициализация Git репозитория

```bash
cd "/Users/kazybek.kassym/Desktop/DAF/BI Analytics System - Saulemai Medical Center/streamlit_dash"

# Инициализация Git
git init

# Добавление всех файлов
git add .

# Первый коммит
git commit -m "Initial commit: Medical Center Management System v3.2.0"
```

### Шаг 2: Создание репозитория на GitHub

1. Зайди на [GitHub.com](https://github.com)
2. Нажми "New repository"
3. Название: `medical-center-management`
4. Описание: `Полная система управления медицинским центром`
5. Выбери "Public" (для бесплатного Streamlit Cloud)
6. НЕ добавляй README, .gitignore, лицензию (они уже есть)
7. Нажми "Create repository"

### Шаг 3: Подключение к GitHub

```bash
# Добавление удаленного репозитория (замени USERNAME на свой GitHub username)
git remote add origin https://github.com/USERNAME/medical-center-management.git

# Переименование основной ветки в main
git branch -M main

# Загрузка в GitHub
git push -u origin main
```

---

## 🌐 ДЕПЛОЙ В STREAMLIT CLOUD

### Шаг 1: Вход в Streamlit Cloud

1. Зайди на [share.streamlit.io](https://share.streamlit.io)
2. Войди через GitHub аккаунт
3. Нажми "New app"

### Шаг 2: Настройка приложения

**Основные настройки:**
- **Repository:** `USERNAME/medical-center-management`
- **Branch:** `main`
- **Main file path:** `app.py`
- **App URL:** `medical-center-management` (или любое свободное имя)

**Дополнительные настройки:**
- **Python version:** 3.9 (рекомендуется)
- **Memory:** 1 GB (достаточно для SQLite)

### Шаг 3: Настройка секретов

В разделе "Secrets" добавь:

```toml
OWNER_PASSWORD = "твой_безопасный_пароль_владельца"
ADMIN_PASSWORD = "твой_безопасный_пароль_админа"
CRM_PASSWORD = "твой_безопасный_пароль_crm"
```

### Шаг 4: Запуск деплоя

1. Нажми "Deploy!"
2. Дождись завершения деплоя (5-10 минут)
3. Получи ссылку на приложение: `https://medical-center-management-USERNAME.streamlit.app`

---

## 🔐 НАСТРОЙКА БЕЗОПАСНОСТИ

### Шаг 1: Смена паролей по умолчанию

**ВАЖНО!** Смени пароли по умолчанию:

```bash
# Генерация безопасных паролей
python generate_secure_passwords.py
```

### Шаг 2: Настройка переменных окружения

В Streamlit Cloud Secrets добавь:

```toml
# Безопасные пароли
OWNER_PASSWORD = "сгенерированный_безопасный_пароль_1"
ADMIN_PASSWORD = "сгенерированный_безопасный_пароль_2"
CRM_PASSWORD = "сгенерированный_безопасный_пароль_3"

# Дополнительные настройки
APP_TITLE = "Медицинский Центр - Система управления"
APP_ICON = "🏥"
```

---

## 📊 МОНИТОРИНГ И ОБСЛУЖИВАНИЕ

### Шаг 1: Мониторинг

- **Логи:** Доступны в Streamlit Cloud Dashboard
- **Использование:** Отслеживай в разделе "Usage"
- **Ошибки:** Проверяй логи при возникновении проблем

### Шаг 2: Обновления

Для обновления приложения:

```bash
# Внеси изменения в код
git add .
git commit -m "Update: описание изменений"
git push origin main

# Streamlit Cloud автоматически перезапустит приложение
```

### Шаг 3: Резервное копирование

- **База данных:** Используй встроенную функцию "Резервные копии"
- **Код:** GitHub автоматически сохраняет все версии
- **Настройки:** Сохрани секреты в безопасном месте

---

## 🚨 УСТРАНЕНИЕ НЕПОЛАДОК

### Проблема 1: Ошибка импорта модулей

**Решение:**
```python
# Убедись, что все модули в корневой папке
# Проверь импорты в app.py
```

### Проблема 2: Ошибка базы данных

**Решение:**
```python
# SQLite файлы создаются автоматически
# Проверь права доступа к файлам
```

### Проблема 3: Медленная загрузка

**Решение:**
- Увеличь Memory в настройках Streamlit Cloud
- Оптимизируй запросы к базе данных
- Используй кэширование

### Проблема 4: Ошибки аутентификации

**Решение:**
- Проверь секреты в Streamlit Cloud
- Убедись, что пароли правильно заданы
- Проверь логи на ошибки

---

## 📱 ДОСТУП К ПРИЛОЖЕНИЮ

### После успешного деплоя:

1. **URL приложения:** `https://medical-center-management-USERNAME.streamlit.app`
2. **Логин:** `admin`
3. **Пароль:** Тот, что указан в секретах
4. **Роли пользователей:**
   - `owner` - полный доступ
   - `admin` - административный доступ
   - `crm` - доступ только к CRM

### Функции системы:

- 🏥 **CRM Система** - управление приемами
- 📊 **Аналитика** - KPI и графики
- 📚 **Справочники** - клиенты, услуги, врачи
- 📋 **Аудит** - логи действий
- 📧 **Уведомления** - система оповещений
- 💾 **Резервные копии** - бэкапы данных
- 📥 **Импорт данных** - загрузка из Excel

---

## 🎯 СЛЕДУЮЩИЕ ШАГИ

### После деплоя:

1. **Тестирование** - проверь все функции
2. **Документация** - создай руководство пользователя
3. **Обучение** - обучи персонал работе с системой
4. **Мониторинг** - отслеживай использование
5. **Обновления** - регулярно обновляй систему

### Возможные улучшения:

- **Интеграция с внешними системами**
- **Мобильное приложение**
- **Расширенная аналитика**
- **Автоматические уведомления**
- **API для интеграций**

---

## 📞 ПОДДЕРЖКА

### Если возникли проблемы:

1. **Проверь логи** в Streamlit Cloud Dashboard
2. **Обратись к документации** Streamlit
3. **Создай issue** в GitHub репозитории
4. **Свяжись с разработчиком** для консультации

---

**Удачи с деплоем! 🚀**

Система готова к использованию в продакшене!
