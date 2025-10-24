#!/usr/bin/env python3
"""
Скрипт миграции базы данных для Jardem Medical Center
Выполняется при каждом запуске приложения для обеспечения совместимости
"""

import sqlite3
import os

def migrate_database():
    """Выполнить миграции базы данных"""
    db_path = 'medical_center.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Выполнение миграций базы данных...")
        
        # Миграция 1: Добавление колонки updated_at в users
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN updated_at TIMESTAMP")
            print("✅ Добавлена колонка updated_at в таблицу users")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка updated_at уже существует в таблице users")
        
        # Миграция 2: Добавление колонки source в appointments
        try:
            cursor.execute("ALTER TABLE appointments ADD COLUMN source TEXT DEFAULT 'прямой'")
            print("✅ Добавлена колонка source в таблицу appointments")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка source уже существует в таблице appointments")
        
        # Миграция 3: Добавление колонки payment_status в appointments
        try:
            cursor.execute("ALTER TABLE appointments ADD COLUMN payment_status TEXT DEFAULT 'не оплачен'")
            print("✅ Добавлена колонка payment_status в таблицу appointments")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка payment_status уже существует в таблице appointments")
        
        # Миграция 4: Создание таблицы appointment_service_payments
        try:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS appointment_service_payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_service_id INTEGER NOT NULL,
                    payment_method TEXT NOT NULL,
                    amount DECIMAL(10,2) NOT NULL,
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (appointment_service_id) REFERENCES appointment_services(id)
                )
            ''')
            print("✅ Создана таблица appointment_service_payments")
        except sqlite3.OperationalError:
            # Таблица уже существует
            print("ℹ️ Таблица appointment_service_payments уже существует")
        
        # Миграция 5: Добавление колонки is_active в clients
        try:
            cursor.execute("ALTER TABLE clients ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✅ Добавлена колонка is_active в таблицу clients")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка is_active уже существует в таблице clients")
        
        # Миграция 6: Добавление колонки is_active в doctors
        try:
            cursor.execute("ALTER TABLE doctors ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✅ Добавлена колонка is_active в таблицу doctors")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка is_active уже существует в таблице doctors")
        
        # Миграция 7: Добавление колонки is_active в services
        try:
            cursor.execute("ALTER TABLE services ADD COLUMN is_active BOOLEAN DEFAULT 1")
            print("✅ Добавлена колонка is_active в таблицу services")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка is_active уже существует в таблице services")
        
        # Миграция 8: Добавление колонки last_login в users
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            print("✅ Добавлена колонка last_login в таблицу users")
        except sqlite3.OperationalError:
            # Колонка уже существует
            print("ℹ️ Колонка last_login уже существует в таблице users")
        
        conn.commit()
        conn.close()
        
        print("✅ Все миграции выполнены успешно!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка выполнения миграций: {e}")
        return False

if __name__ == "__main__":
    migrate_database()