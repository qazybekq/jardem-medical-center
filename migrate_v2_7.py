#!/usr/bin/env python3
"""
Миграция базы данных для версии 2.7
Добавляет поля для источника пациента
"""

import sqlite3
import sys

def migrate_database():
    """Миграция БД для v2.7"""
    try:
        conn = sqlite3.connect('medical_center.db')
        cursor = conn.cursor()
        
        print("🔄 Начинаем миграцию БД для v2.7...")
        
        # 1. Добавляем поле source в таблицу appointments
        try:
            cursor.execute('''
                ALTER TABLE appointments 
                ADD COLUMN source VARCHAR(100) DEFAULT 'Повторное посещение'
            ''')
            print("✅ Добавлено поле 'source' в таблицу appointments")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print("ℹ️  Поле 'source' уже существует в таблице appointments")
            else:
                raise
        
        # 2. Создаем таблицу для оплат по каждой услуге
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS appointment_service_payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                appointment_service_id INTEGER NOT NULL,
                payment_method VARCHAR(50) NOT NULL,
                amount DECIMAL(10,2) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (appointment_service_id) REFERENCES appointment_services(id) ON DELETE CASCADE
            )
        ''')
        print("✅ Создана таблица 'appointment_service_payments'")
        
        # 3. Добавляем поле payment_status в таблицу appointments
        try:
            cursor.execute('''
                ALTER TABLE appointments 
                ADD COLUMN payment_status VARCHAR(50) DEFAULT 'не оплачено'
            ''')
            print("✅ Добавлено поле 'payment_status' в таблицу appointments")
        except sqlite3.OperationalError as e:
            if 'duplicate column name' in str(e).lower():
                print("ℹ️  Поле 'payment_status' уже существует в таблице appointments")
            else:
                raise
        
        conn.commit()
        print("✅ Миграция завершена успешно!")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

if __name__ == "__main__":
    success = migrate_database()
    sys.exit(0 if success else 1)

