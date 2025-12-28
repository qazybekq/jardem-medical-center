#!/usr/bin/env python3
"""
Скрипт для импорта данных из файла саулемай-2.xlsx
- Удаляет старые данные (врачи и услуги)
- Импортирует новых врачей и услуги с ценами
"""

import pandas as pd
import sqlite3
from datetime import datetime
import re

def parse_doctor_name(full_name):
    """Парсит полное имя врача на имя и фамилию"""
    if pd.isna(full_name):
        return None, None
    
    full_name = str(full_name).strip()
    
    # Если имя в формате "Фамилия И.О." или "Фамилия Имя Отчество"
    parts = full_name.split()
    
    if len(parts) >= 2:
        # Первая часть - фамилия, остальное - имя
        last_name = parts[0]
        first_name = ' '.join(parts[1:])
        return first_name, last_name
    else:
        # Если только одна часть, считаем её фамилией
        return "", full_name

def parse_price(price_str):
    """Парсит цену, обрабатывает диапазоны"""
    if pd.isna(price_str):
        return None
    
    price_str = str(price_str).strip()
    
    # Обработка диапазонов типа "10000-15000"
    if '-' in price_str:
        parts = price_str.split('-')
        try:
            # Берем среднее значение диапазона
            min_price = float(re.sub(r'[^\d.]', '', parts[0]))
            max_price = float(re.sub(r'[^\d.]', '', parts[1]))
            return round((min_price + max_price) / 2, 2)
        except:
            try:
                return float(re.sub(r'[^\d.]', '', parts[0]))
            except:
                return None
    
    # Удаляем все нецифровые символы кроме точки
    price_str = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(price_str)
    except:
        return None

def import_saulemai_data():
    """Основная функция импорта"""
    print("=" * 80)
    print("ИМПОРТ ДАННЫХ ИЗ ФАЙЛА саулемай-2.xlsx")
    print("=" * 80)
    
    # Подключение к базе данных
    conn = sqlite3.connect('medical_center.db')
    cursor = conn.cursor()
    
    try:
        # Читаем Excel файл
        print("\n1. Чтение файла Excel...")
        df = pd.read_excel('саулемай-2.xlsx', sheet_name='Лист1')
        
        # Удаляем пустые строки
        df = df.dropna(subset=['Услуга', 'врач'])
        df = df[df['Услуга'].notna() & df['врач'].notna()]
        
        print(f"   ✓ Найдено строк с данными: {len(df)}")
        
        # Инициализация базы данных (если нужно)
        print("\n2. Инициализация базы данных...")
        # Создаем таблицы напрямую, без импорта database.py
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price DECIMAL(10,2) NOT NULL,
                duration_minutes INTEGER DEFAULT 30,
                doctor_id INTEGER,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (doctor_id) REFERENCES doctors (id)
            )
        ''')
        
        conn.commit()
        print("   ✓ База данных инициализирована")
        
        # Удаление старых данных
        print("\n3. Удаление старых данных...")
        # Проверяем существование таблиц перед удалением
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        
        tables_to_clear = [
            'appointment_service_payments',
            'appointment_services', 
            'appointments',
            'services',
            'doctors'
        ]
        
        for table in tables_to_clear:
            if table in existing_tables:
                cursor.execute(f"DELETE FROM {table}")
                print(f"   ✓ Очищена таблица: {table}")
        
        conn.commit()
        print("   ✓ Старые данные удалены")
        
        # Извлечение уникальных врачей
        print("\n4. Обработка врачей...")
        # Убираем дубликаты по имени врача (нормализуем пробелы)
        df['врач_normalized'] = df['врач'].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
        doctors_df = df[['врач_normalized', 'специальность']].drop_duplicates(subset=['врач_normalized'], keep='first')
        doctors_dict = {}  # Словарь для хранения ID врачей
        
        for idx, row in doctors_df.iterrows():
            doctor_name = str(row['врач_normalized']).strip()
            specialization = str(row['специальность']).strip() if pd.notna(row['специальность']) else 'Не указана'
            
            first_name, last_name = parse_doctor_name(doctor_name)
            
            # Проверяем, не существует ли уже такой врач
            cursor.execute('''
                SELECT id FROM doctors 
                WHERE last_name = ? AND first_name = ? AND specialization = ?
            ''', (last_name, first_name, specialization))
            existing = cursor.fetchone()
            
            if existing:
                doctor_id = existing[0]
                print(f"   ⚠ Врач уже существует: {last_name} {first_name} ({specialization}) - ID: {doctor_id}")
            else:
                # Вставляем врача в базу
                cursor.execute('''
                    INSERT INTO doctors (first_name, last_name, specialization, phone, email, is_active)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    first_name,
                    last_name,
                    specialization,
                    '70000000000',  # Заглушка для телефона
                    '',  # Пустой email
                    1  # is_active
                ))
                doctor_id = cursor.lastrowid
                print(f"   ✓ Добавлен врач: {last_name} {first_name} ({specialization})")
            
            doctors_dict[doctor_name] = doctor_id
        
        print(f"   ✓ Всего врачей добавлено: {len(doctors_dict)}")
        
        # Импорт услуг
        print("\n5. Импорт услуг...")
        services_count = 0
        
        for idx, row in df.iterrows():
            service_name = str(row['Услуга']).strip()
            doctor_name = str(row['врач_normalized']).strip() if 'врач_normalized' in row else str(row['врач']).strip()
            price = parse_price(row['Стоимость'])
            
            if not service_name or not doctor_name:
                continue
            
            if doctor_name not in doctors_dict:
                print(f"   ⚠ Врач '{doctor_name}' не найден, пропускаем услугу '{service_name}'")
                continue
            
            if price is None:
                print(f"   ⚠ Не удалось распарсить цену для услуги '{service_name}', пропускаем")
                continue
            
            doctor_id = doctors_dict[doctor_name]
            
            # Вставляем услугу
            cursor.execute('''
                INSERT INTO services (name, description, price, duration_minutes, doctor_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                service_name,
                f"Услуга: {service_name}",  # Описание
                price,
                30,  # Длительность по умолчанию
                doctor_id,
                1  # is_active
            ))
            
            services_count += 1
            print(f"   ✓ Услуга: {service_name} - {price} тг (Врач: {doctor_name})")
        
        print(f"   ✓ Всего услуг добавлено: {services_count}")
        
        # Сохранение изменений
        conn.commit()
        print("\n" + "=" * 80)
        print("✅ ИМПОРТ УСПЕШНО ЗАВЕРШЕН!")
        print("=" * 80)
        print(f"Врачей: {len(doctors_dict)}")
        print(f"Услуг: {services_count}")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ ОШИБКА ПРИ ИМПОРТЕ: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    import_saulemai_data()

