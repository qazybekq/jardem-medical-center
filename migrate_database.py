#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления недостающих колонок
"""

import sqlite3
import os

def migrate_database():
    """Миграция базы данных для добавления недостающих колонок"""
    
    db_path = "medical_center.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена. Создайте базу данных сначала.")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Начинаем миграцию базы данных...")
        
        # Проверяем существование колонки source
        cursor.execute("PRAGMA table_info(appointments)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'source' not in columns:
            print("➕ Добавляем колонку source в таблицу appointments...")
            cursor.execute("ALTER TABLE appointments ADD COLUMN source TEXT DEFAULT 'прямой'")
            print("✅ Колонка source добавлена")
        else:
            print("✅ Колонка source уже существует")
        
        if 'payment_status' not in columns:
            print("➕ Добавляем колонку payment_status в таблицу appointments...")
            cursor.execute("ALTER TABLE appointments ADD COLUMN payment_status TEXT DEFAULT 'не оплачен'")
            print("✅ Колонка payment_status добавлена")
        else:
            print("✅ Колонка payment_status уже существует")
        
        # Обновляем существующие записи
        print("🔄 Обновляем существующие записи...")
        cursor.execute("UPDATE appointments SET source = 'прямой' WHERE source IS NULL")
        cursor.execute("UPDATE appointments SET payment_status = 'не оплачен' WHERE payment_status IS NULL")
        
        conn.commit()
        print("✅ Миграция завершена успешно!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    migrate_database()
