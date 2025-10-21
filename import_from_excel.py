#!/usr/bin/env python3
"""
Скрипт для импорта данных из Excel файлов в базу данных
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os

DB_NAME = 'medical_center.db'
TEMPLATE_DIR = 'excel_templates'

def get_connection():
    """Получить соединение с базой данных"""
    return sqlite3.connect(DB_NAME)

def import_clients(file_path):
    """Импорт клиентов из Excel"""
    print("\n" + "=" * 60)
    print("📋 Импорт клиентов...")
    print("=" * 60)
    
    df = pd.read_excel(file_path)
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO clients (first_name, last_name, birth_date, phone, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row['first_name'],
                row['last_name'],
                row['birth_date'],
                row['phone'],
                row.get('email', '')
            ))
            success_count += 1
            print(f"   ✅ {row['first_name']} {row['last_name']} - добавлен")
        except sqlite3.IntegrityError as e:
            error_count += 1
            print(f"   ❌ {row['first_name']} {row['last_name']} - ошибка: {e}")
        except Exception as e:
            error_count += 1
            print(f"   ❌ Строка {idx + 2} - ошибка: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Результат: {success_count} успешно, {error_count} ошибок")
    return success_count, error_count

def import_doctors(file_path):
    """Импорт врачей из Excel"""
    print("\n" + "=" * 60)
    print("👨‍⚕️ Импорт врачей...")
    print("=" * 60)
    
    df = pd.read_excel(file_path)
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            cursor.execute('''
                INSERT INTO doctors (first_name, last_name, specialization, phone, email)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                row['first_name'],
                row['last_name'],
                row['specialization'],
                row['phone'],
                row.get('email', '')
            ))
            success_count += 1
            print(f"   ✅ {row['first_name']} {row['last_name']} ({row['specialization']}) - добавлен")
        except sqlite3.IntegrityError as e:
            error_count += 1
            print(f"   ❌ {row['first_name']} {row['last_name']} - ошибка: {e}")
        except Exception as e:
            error_count += 1
            print(f"   ❌ Строка {idx + 2} - ошибка: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Результат: {success_count} успешно, {error_count} ошибок")
    return success_count, error_count

def import_services(file_path):
    """Импорт услуг из Excel"""
    print("\n" + "=" * 60)
    print("🏥 Импорт услуг...")
    print("=" * 60)
    
    df = pd.read_excel(file_path)
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Находим ID врача по фамилии
            cursor.execute('SELECT id FROM doctors WHERE last_name = ?', (row['doctor_last_name'],))
            doctor = cursor.fetchone()
            
            if not doctor:
                error_count += 1
                print(f"   ❌ {row['name']} - врач с фамилией '{row['doctor_last_name']}' не найден")
                continue
            
            doctor_id = doctor[0]
            
            cursor.execute('''
                INSERT INTO services (name, price, doctor_id, duration_minutes)
                VALUES (?, ?, ?, ?)
            ''', (
                row['name'],
                row['price'],
                doctor_id,
                row['duration_minutes']
            ))
            success_count += 1
            print(f"   ✅ {row['name']} ({row['price']} ₸) - добавлена")
        except Exception as e:
            error_count += 1
            print(f"   ❌ Строка {idx + 2} - ошибка: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Результат: {success_count} успешно, {error_count} ошибок")
    return success_count, error_count

def import_appointments(file_path):
    """Импорт приемов из Excel"""
    print("\n" + "=" * 60)
    print("📅 Импорт приемов...")
    print("=" * 60)
    
    df = pd.read_excel(file_path)
    conn = get_connection()
    cursor = conn.cursor()
    
    success_count = 0
    error_count = 0
    
    for idx, row in df.iterrows():
        try:
            # Находим ID клиента по фамилии
            cursor.execute('SELECT id FROM clients WHERE last_name = ?', (row['client_last_name'],))
            client = cursor.fetchone()
            if not client:
                error_count += 1
                print(f"   ❌ Строка {idx + 2} - клиент '{row['client_last_name']}' не найден")
                continue
            
            # Находим ID врача по фамилии
            cursor.execute('SELECT id FROM doctors WHERE last_name = ?', (row['doctor_last_name'],))
            doctor = cursor.fetchone()
            if not doctor:
                error_count += 1
                print(f"   ❌ Строка {idx + 2} - врач '{row['doctor_last_name']}' не найден")
                continue
            
            # Находим ID услуги по названию
            cursor.execute('SELECT id FROM services WHERE name = ?', (row['service_name'],))
            service = cursor.fetchone()
            if not service:
                error_count += 1
                print(f"   ❌ Строка {idx + 2} - услуга '{row['service_name']}' не найдена")
                continue
            
            cursor.execute('''
                INSERT INTO appointments (client_id, doctor_id, service_id, appointment_date, 
                                        appointment_time, status, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                client[0],
                doctor[0],
                service[0],
                row['appointment_date'],
                row['appointment_time'],
                row['status'],
                row.get('notes', '')
            ))
            success_count += 1
            print(f"   ✅ {row['appointment_date']} {row['appointment_time']} - {row['client_last_name']} → {row['doctor_last_name']}")
        except Exception as e:
            error_count += 1
            print(f"   ❌ Строка {idx + 2} - ошибка: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n📊 Результат: {success_count} успешно, {error_count} ошибок")
    return success_count, error_count

def main():
    """Основная функция импорта"""
    print("\n" + "=" * 60)
    print("🚀 ИМПОРТ ДАННЫХ ИЗ EXCEL В БАЗУ ДАННЫХ")
    print("=" * 60)
    
    # Проверяем наличие папки с шаблонами
    if not os.path.exists(TEMPLATE_DIR):
        print(f"\n❌ Ошибка: папка '{TEMPLATE_DIR}' не найдена!")
        print(f"   Сначала запустите: python create_excel_templates.py")
        return
    
    # Проверяем наличие базы данных
    if not os.path.exists(DB_NAME):
        print(f"\n❌ Ошибка: база данных '{DB_NAME}' не найдена!")
        print(f"   Сначала запустите приложение: streamlit run app.py")
        return
    
    # Статистика
    total_success = 0
    total_errors = 0
    
    # 1. Импортируем клиентов
    clients_file = f'{TEMPLATE_DIR}/1_clients_template.xlsx'
    if os.path.exists(clients_file):
        success, errors = import_clients(clients_file)
        total_success += success
        total_errors += errors
    else:
        print(f"\n⚠️ Файл {clients_file} не найден, пропускаем...")
    
    # 2. Импортируем врачей
    doctors_file = f'{TEMPLATE_DIR}/2_doctors_template.xlsx'
    if os.path.exists(doctors_file):
        success, errors = import_doctors(doctors_file)
        total_success += success
        total_errors += errors
    else:
        print(f"\n⚠️ Файл {doctors_file} не найден, пропускаем...")
    
    # 3. Импортируем услуги
    services_file = f'{TEMPLATE_DIR}/3_services_template.xlsx'
    if os.path.exists(services_file):
        success, errors = import_services(services_file)
        total_success += success
        total_errors += errors
    else:
        print(f"\n⚠️ Файл {services_file} не найден, пропускаем...")
    
    # 4. Импортируем приемы
    appointments_file = f'{TEMPLATE_DIR}/4_appointments_template.xlsx'
    if os.path.exists(appointments_file):
        success, errors = import_appointments(appointments_file)
        total_success += success
        total_errors += errors
    else:
        print(f"\n⚠️ Файл {appointments_file} не найден, пропускаем...")
    
    # Итоговая статистика
    print("\n" + "=" * 60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА")
    print("=" * 60)
    print(f"\n✅ Успешно импортировано: {total_success} записей")
    print(f"❌ Ошибок: {total_errors}")
    
    if total_errors == 0:
        print("\n🎉 Все данные импортированы успешно!")
    else:
        print(f"\n⚠️ Импорт завершен с {total_errors} ошибками")
        print("   Проверьте сообщения выше для деталей")
    
    # Показываем текущее состояние базы
    print("\n" + "=" * 60)
    print("📊 ТЕКУЩЕЕ СОСТОЯНИЕ БАЗЫ ДАННЫХ")
    print("=" * 60)
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM clients')
    clients_count = cursor.fetchone()[0]
    print(f"\n👥 Клиенты: {clients_count}")
    
    cursor.execute('SELECT COUNT(*) FROM doctors')
    doctors_count = cursor.fetchone()[0]
    print(f"👨‍⚕️ Врачи: {doctors_count}")
    
    cursor.execute('SELECT COUNT(*) FROM services')
    services_count = cursor.fetchone()[0]
    print(f"🏥 Услуги: {services_count}")
    
    cursor.execute('SELECT COUNT(*) FROM appointments')
    appointments_count = cursor.fetchone()[0]
    print(f"📅 Приемы: {appointments_count}")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Импорт завершен!")
    print("=" * 60)
    print("\n💡 Теперь откройте приложение: streamlit run app.py")

if __name__ == "__main__":
    main()

