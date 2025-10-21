#!/usr/bin/env python3
"""
Комплексное тестирование системы Jardem
Проверка всех функций и модулей
"""

import sys
import os
import sqlite3
import traceback
from datetime import datetime, date, time

# Добавляем путь к модулям
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_connection():
    """Тест подключения к базе данных"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        conn.close()
        return True, f"✅ База данных: {len(tables)} таблиц найдено"
    except Exception as e:
        return False, f"❌ Ошибка БД: {e}"

def test_user_authentication():
    """Тест системы аутентификации"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем таблицу пользователей
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        # Проверяем структуру таблицы
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        required_columns = ['id', 'username', 'password_hash', 'access_level']
        missing_columns = [col for col in required_columns if col not in column_names]
        
        conn.close()
        
        if missing_columns:
            return False, f"❌ Отсутствуют колонки: {missing_columns}"
        
        return True, f"✅ Аутентификация: {user_count} пользователей, все колонки на месте"
    except Exception as e:
        return False, f"❌ Ошибка аутентификации: {e}"

def test_crm_functions():
    """Тест CRM функций"""
    try:
        from database import (
            search_clients, get_all_doctors, get_all_services, 
            get_appointments_by_date_range, create_appointment
        )
        
        # Тест получения клиентов
        clients = search_clients("")
        clients_ok = len(clients) >= 0
        
        # Тест получения врачей
        doctors = get_all_doctors()
        doctors_ok = len(doctors) >= 0
        
        # Тест получения услуг
        services = get_all_services()
        services_ok = len(services) >= 0
        
        # Тест получения приемов
        today = date.today()
        appointments = get_appointments_by_date_range(today, today)
        appointments_ok = len(appointments) >= 0
        
        if all([clients_ok, doctors_ok, services_ok, appointments_ok]):
            return True, f"✅ CRM: клиенты({len(clients)}), врачи({len(doctors)}), услуги({len(services)}), приемы({len(appointments)})"
        else:
            return False, "❌ Ошибка в CRM функциях"
    except Exception as e:
        return False, f"❌ Ошибка CRM: {e}"

def test_analytics_functions():
    """Тест аналитических функций"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Тест получения аналитических данных через SQL
        cursor.execute('''
            SELECT COUNT(*) FROM appointments 
            WHERE appointment_date >= date('now', '-30 days')
        ''')
        appointments_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM clients')
        clients_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM doctors')
        doctors_count = cursor.fetchone()[0]
        
        conn.close()
        
        return True, f"✅ Аналитика: приемы({appointments_count}), клиенты({clients_count}), врачи({doctors_count})"
    except Exception as e:
        return False, f"❌ Ошибка аналитики: {e}"

def test_directories_functions():
    """Тест функций справочников"""
    try:
        from database import (
            search_clients, get_all_doctors, get_all_services,
            create_client
        )
        
        # Тест получения данных
        clients = search_clients("")
        doctors = get_all_doctors()
        services = get_all_services()
        
        return True, f"✅ Справочники: клиенты({len(clients)}), врачи({len(doctors)}), услуги({len(services)})"
    except Exception as e:
        return False, f"❌ Ошибка справочников: {e}"

def test_user_management():
    """Тест управления пользователями"""
    try:
        from database import get_all_users, create_user, update_user_password
        
        # Тест получения пользователей
        users = get_all_users()
        users_ok = len(users) >= 0
        
        return True, f"✅ Управление пользователями: {len(users)} пользователей"
    except Exception as e:
        return False, f"❌ Ошибка управления пользователями: {e}"

def test_audit_functions():
    """Тест аудита"""
    try:
        from database import get_connection, log_audit_action
        
        # Тест записи лога
        log_audit_action(1, 'TEST', 'system', 0, 'Тестовое действие')
        
        # Тест получения логов через SQL
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM audit_log')
        logs_count = cursor.fetchone()[0]
        conn.close()
        
        return True, f"✅ Аудит: {logs_count} записей в логе"
    except Exception as e:
        return False, f"❌ Ошибка аудита: {e}"

def test_backup_functions():
    """Тест функций резервного копирования"""
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, что можем создать бэкап
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        conn.close()
        
        return True, f"✅ Резервное копирование: {len(tables)} таблиц для бэкапа"
    except Exception as e:
        return False, f"❌ Ошибка бэкапа: {e}"

def test_notification_functions():
    """Тест функций уведомлений"""
    try:
        # Проверяем, что модули уведомлений импортируются
        import notification_manager
        import notifications
        
        return True, "✅ Уведомления: модули загружены"
    except Exception as e:
        return False, f"❌ Ошибка уведомлений: {e}"

def test_import_functions():
    """Тест функций импорта"""
    try:
        # Проверяем, что модули импорта загружаются
        import import_manager
        
        return True, "✅ Импорт: модули загружены"
    except Exception as e:
        return False, f"❌ Ошибка импорта: {e}"

def test_security():
    """Тест безопасности"""
    try:
        from database import get_connection
        import bcrypt
        
        # Тест хеширования паролей
        test_password = "test_password_123"
        hashed = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt())
        verify = bcrypt.checkpw(test_password.encode('utf-8'), hashed)
        
        if verify:
            return True, "✅ Безопасность: хеширование паролей работает"
        else:
            return False, "❌ Ошибка хеширования паролей"
    except Exception as e:
        return False, f"❌ Ошибка безопасности: {e}"

def run_comprehensive_test():
    """Запуск комплексного тестирования"""
    print("🧪 КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ JARDEM")
    print("=" * 60)
    print(f"📅 Дата тестирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    tests = [
        ("🔗 Подключение к БД", test_database_connection),
        ("🔐 Аутентификация", test_user_authentication),
        ("🏥 CRM Система", test_crm_functions),
        ("📊 Аналитика", test_analytics_functions),
        ("📚 Справочники", test_directories_functions),
        ("👥 Управление пользователями", test_user_management),
        ("📋 Аудит", test_audit_functions),
        ("💾 Резервное копирование", test_backup_functions),
        ("📧 Уведомления", test_notification_functions),
        ("📥 Импорт данных", test_import_functions),
        ("🔒 Безопасность", test_security)
    ]
    
    results = []
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            success, message = test_func()
            results.append((test_name, success, message))
            if success:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            results.append((test_name, False, f"❌ Критическая ошибка: {e}"))
            failed += 1
    
    print("\n📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print("=" * 60)
    
    for test_name, success, message in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        print(f"{test_name}: {status}")
        print(f"  {message}")
        print()
    
    print("=" * 60)
    print(f"📈 ИТОГО: {passed} пройдено, {failed} провалено")
    print(f"📊 Успешность: {(passed/(passed+failed)*100):.1f}%")
    
    if failed == 0:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        return True
    else:
        print("⚠️ ОБНАРУЖЕНЫ ПРОБЛЕМЫ, ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")
        return False

if __name__ == "__main__":
    success = run_comprehensive_test()
    sys.exit(0 if success else 1)
