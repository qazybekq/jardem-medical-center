#!/usr/bin/env python3
"""
Модуль для работы с базой данных версии 2.0
Новая структура: отдельные таблицы для клиентов, врачей, услуг, приемов
"""

import sqlite3
import bcrypt
from datetime import datetime
import streamlit as st
import os
import json
from validators import (
    validate_search_query, validate_phone, validate_email,
    validate_date, validate_name, validate_notes, ValidationError
)

def init_database():
    """Инициализация базы данных версии 2.0"""
    conn = sqlite3.connect('medical_center.db')
    cursor = conn.cursor()
    
    # Таблица пользователей системы
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            access_level TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_login TIMESTAMP
        )
    ''')
    
    # Таблица клиентов (пациентов)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT,  -- НЕОБЯЗАТЕЛЬНОЕ поле
            birth_date DATE,
            phone TEXT NOT NULL,
            email TEXT,
            is_active BOOLEAN DEFAULT 1,  -- Добавляем поле активности
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Миграция: добавляем поле is_active в clients если его нет
    try:
        cursor.execute("ALTER TABLE clients ADD COLUMN is_active BOOLEAN DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    # Таблица врачей
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

    # Миграция: добавляем поле is_active в doctors если его нет
    try:
        cursor.execute("ALTER TABLE doctors ADD COLUMN is_active BOOLEAN DEFAULT 1")
    except sqlite3.OperationalError:
        pass  # Поле уже существует
    
    # Таблица услуг
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
    
    # Таблица приемов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            doctor_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            appointment_date DATE NOT NULL,
            appointment_time TIME NOT NULL,
            status TEXT DEFAULT 'записан',
            notes TEXT,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            actual_duration_minutes INTEGER,
            source TEXT DEFAULT 'прямой',
            payment_status TEXT DEFAULT 'не оплачен',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients (id),
            FOREIGN KEY (doctor_id) REFERENCES doctors (id),
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
    ''')
    
    # Таблица связи приемов и услуг (многие-ко-многим)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            price DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (appointment_id) REFERENCES appointments (id) ON DELETE CASCADE,
            FOREIGN KEY (service_id) REFERENCES services (id),
            UNIQUE(appointment_id, service_id)
        )
    ''')
    
    # Таблица платежей за услуги в приемах
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointment_service_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            appointment_service_id INTEGER NOT NULL,
            payment_method TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (appointment_service_id) REFERENCES appointment_services (id) ON DELETE CASCADE
        )
    ''')
    
    # Таблица аудита действий
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица настроек
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Миграция: добавление колонки last_login если её нет
    try:
        cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
        print("✅ Добавлена колонка last_login в таблицу users")
    except sqlite3.OperationalError:
        # Колонка уже существует
        pass
    
    # Миграция: добавление колонки source в appointments если её нет
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN source TEXT DEFAULT 'прямой'")
        print("✅ Добавлена колонка source в таблицу appointments")
    except sqlite3.OperationalError:
        # Колонка уже существует
        pass
    
    # Миграция: добавление колонки payment_status в appointments если её нет
    try:
        cursor.execute("ALTER TABLE appointments ADD COLUMN payment_status TEXT DEFAULT 'не оплачен'")
        print("✅ Добавлена колонка payment_status в таблицу appointments")
    except sqlite3.OperationalError:
        # Колонка уже существует
        pass
    
    conn.commit()
    conn.close()

def create_default_users():
    """Создание пользователей по умолчанию с паролями из переменных окружения"""
    conn = sqlite3.connect('medical_center.db')
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже пользователи
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Получаем пароли из переменных окружения или используем значения по умолчанию
    # ⚠️ В продакшене ОБЯЗАТЕЛЬНО установите переменные окружения!
    owner_password = os.getenv('OWNER_PASSWORD', 'owner123')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    crm_password = os.getenv('CRM_PASSWORD', 'crm123')
    
    # Предупреждаем если используются пароли по умолчанию
    if os.getenv('OWNER_PASSWORD') is None or os.getenv('ADMIN_PASSWORD') is None:
        if hasattr(st, 'warning'):
            st.warning("⚠️ ВНИМАНИЕ: Используются пароли по умолчанию! Установите переменные окружения OWNER_PASSWORD, ADMIN_PASSWORD, CRM_PASSWORD")
        print("⚠️ SECURITY WARNING: Using default passwords! Set environment variables in production!")
    
    # Создаем пользователей
    users = [
        ('owner', owner_password, 'Владелец системы', 'owner'),
        ('admin', admin_password, 'Администратор', 'admin'),
        ('crm_user', crm_password, 'CRM Пользователь', 'crm')
    ]
    
    for username, password, name, access_level in users:
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, access_level)
            VALUES (?, ?, ?, ?)
        ''', (username, password_hash, name, access_level))
    
    conn.commit()
    conn.close()

def migrate_old_appointments():
    """Миграция старых приемов в новую структуру с appointment_services"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Найти приемы без услуг в appointment_services
        cursor.execute('''
            SELECT a.id, a.service_id, s.price
            FROM appointments a
            LEFT JOIN appointment_services aps ON a.id = aps.appointment_id AND a.service_id = aps.service_id
            JOIN services s ON a.service_id = s.id
            WHERE aps.id IS NULL
        ''')
        
        missing = cursor.fetchall()
        
        if missing:
            print(f"🔄 Миграция: найдено {len(missing)} приемов без услуг в appointment_services")
            
            # Добавить недостающие услуги
            for apt_id, service_id, price in missing:
                cursor.execute('''
                    INSERT OR IGNORE INTO appointment_services (appointment_id, service_id, price)
                    VALUES (?, ?, ?)
                ''', (apt_id, service_id, price))
            
            conn.commit()
            print(f"✅ Миграция завершена: добавлено {len(missing)} записей")
        else:
            print("✅ Миграция не требуется: все приемы имеют услуги")
        
        conn.close()
    except Exception as e:
        conn.close()
        print(f"❌ Ошибка миграции: {e}")

def create_default_data():
    """Создание тестовых данных"""
    conn = sqlite3.connect('medical_center.db')
    cursor = conn.cursor()
    
    # Проверяем, есть ли уже данные
    cursor.execute('SELECT COUNT(*) FROM doctors')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # Создаем врачей
    doctors = [
        ('Айгуль', 'Нурланова', 'Терапевт', '+7 777 123 4567', 'aigul@clinic.kz'),
        ('Марат', 'Ахметов', 'Кардиолог', '+7 777 234 5678', 'marat@clinic.kz'),
        ('Айша', 'Калиева', 'Невролог', '+7 777 345 6789', 'aisha@clinic.kz'),
        ('Данияр', 'Сериков', 'Ортопед', '+7 777 456 7890', 'daniyar@clinic.kz'),
        ('Жанар', 'Тулеуова', 'Гинеколог', '+7 777 567 8901', 'zhanar@clinic.kz')
    ]
    
    for first_name, last_name, specialization, phone, email in doctors:
        cursor.execute('''
            INSERT INTO doctors (first_name, last_name, specialization, phone, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, specialization, phone, email))
    
    # Создаем услуги
    services = [
        ('Консультация терапевта', 'Первичная консультация терапевта', 5000, 30, 1),
        ('ЭКГ', 'Электрокардиограмма', 3000, 15, 2),
        ('УЗИ сердца', 'Ультразвуковое исследование сердца', 8000, 45, 2),
        ('Консультация невролога', 'Первичная консультация невролога', 6000, 40, 3),
        ('Рентген позвоночника', 'Рентгенологическое исследование позвоночника', 4000, 20, 4),
        ('Консультация гинеколога', 'Первичная консультация гинеколога', 7000, 35, 5),
        ('УЗИ органов малого таза', 'Ультразвуковое исследование', 6000, 30, 5)
    ]
    
    for name, description, price, duration, doctor_id in services:
        cursor.execute('''
            INSERT INTO services (name, description, price, duration_minutes, doctor_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, description, price, duration, doctor_id))
    
    # Создаем тестовых клиентов
    clients = [
        ('Айжан', 'Нурланова', '1990-05-15', '+7 701 111 1111', 'aizhan@email.com'),
        ('Марат', 'Ахметов', '1985-03-22', '+7 701 222 2222', 'marat@email.com'),
        ('Айша', 'Калиева', '1992-07-10', '+7 701 333 3333', 'aisha@email.com'),
        ('Данияр', 'Сериков', '1988-11-05', '+7 701 444 4444', 'daniyar@email.com'),
        ('Жанар', 'Тулеуова', '1995-09-18', '+7 701 555 5555', 'zhanar@email.com'),
        ('Асхат', 'Ибрагимов', '1987-12-03', '+7 701 666 6666', 'askhat@email.com'),
        ('Гульнара', 'Сейтжанова', '1991-04-25', '+7 701 777 7777', 'gulnara@email.com'),
        ('Ерлан', 'Куанов', '1989-08-14', '+7 701 888 8888', 'erlan@email.com')
    ]
    
    for first_name, last_name, birth_date, phone, email in clients:
        cursor.execute('''
            INSERT INTO clients (first_name, last_name, birth_date, phone, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, birth_date, phone, email))
    
    conn.commit()
    conn.close()

def get_connection():
    """Получить соединение с базой данных с обработкой ошибок"""
    try:
        conn = sqlite3.connect('medical_center.db', timeout=10)
        # Включаем foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    except sqlite3.Error as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка подключения к базе данных: {e}")
        raise RuntimeError(f"Не удалось подключиться к БД: {e}")

def search_clients(query):
    """Поиск клиентов по имени, фамилии или телефону с валидацией"""
    try:
        # Валидация поискового запроса
        query = validate_search_query(query)
    except ValidationError as e:
        if hasattr(st, 'warning'):
            st.warning(f"⚠️ {str(e)}")
        return []
    
    conn = get_connection()
    cursor = conn.cursor()
    
    search_term = f"%{query}%"
    cursor.execute('''
        SELECT id, first_name, last_name, birth_date, phone, email
        FROM clients
        WHERE first_name LIKE ? OR last_name LIKE ? OR phone LIKE ?
        ORDER BY last_name, first_name
        LIMIT 10
    ''', (search_term, search_term, search_term))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_client_by_id(client_id):
    """Получить клиента по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, first_name, last_name, birth_date, phone, email
        FROM clients
        WHERE id = ?
    ''', (client_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def create_client(first_name, last_name, birth_date, phone, email=None):
    """Создать нового клиента с валидацией"""
    try:
        # Валидация входных данных
        first_name = validate_name(first_name, "Имя")
        last_name = validate_name(last_name, "Фамилия")
        phone = validate_phone(phone)
        email = validate_email(email) if email else None
    except ValidationError as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка валидации: {e}")
        return None
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO clients (first_name, last_name, birth_date, phone, email)
            VALUES (?, ?, ?, ?, ?)
        ''', (first_name, last_name, birth_date, phone, email))
        
        client_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return client_id
    except sqlite3.IntegrityError as e:
        conn.close()
        if hasattr(st, 'error'):
            st.error(f"❌ Телефон уже существует в базе данных")
        return None
    except sqlite3.Error as e:
        conn.close()
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка создания клиента: {e}")
        return None

@st.cache_data(ttl=300)  # Кеш на 5 минут
def get_all_doctors():
    """Получить всех врачей"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, first_name, last_name, specialization, phone, email
        FROM doctors
        WHERE is_active = 1
        ORDER BY last_name, first_name
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

@st.cache_data(ttl=300)  # Кеш на 5 минут
def get_services_by_doctor(doctor_id):
    """Получить услуги по врачу"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, name, description, price, duration_minutes
        FROM services
        WHERE doctor_id = ? AND is_active = 1
        ORDER BY name
    ''', (doctor_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

@st.cache_data(ttl=300)  # Кеш на 5 минут
def get_all_services():
    """Получить все активные услуги"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT s.id, s.name, s.description, s.price, s.duration_minutes, 
               d.first_name, d.last_name, d.specialization
        FROM services s
        JOIN doctors d ON s.doctor_id = d.id
        WHERE s.is_active = 1 AND d.is_active = 1
        ORDER BY d.last_name, d.first_name, s.name
    ''')
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def add_service_to_appointment(appointment_id, service_id, price):
    """Добавить услугу к приему"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO appointment_services (appointment_id, service_id, price)
            VALUES (?, ?, ?)
        ''', (appointment_id, service_id, price))
        
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        # Услуга уже добавлена
        conn.close()
        return False
    except sqlite3.Error as e:
        conn.close()
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка добавления услуги: {e}")
        return False

def remove_service_from_appointment(appointment_id, service_id):
    """Удалить услугу из приема"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM appointment_services
            WHERE appointment_id = ? AND service_id = ?
        ''', (appointment_id, service_id))
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        return affected > 0
    except sqlite3.Error as e:
        conn.close()
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка удаления услуги: {e}")
        return False

def get_appointment_services(appointment_id):
    """Получить все услуги приема"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT aps.id, s.id, s.name, s.description, aps.price, s.price as base_price,
               s.duration_minutes, d.first_name, d.last_name
        FROM appointment_services aps
        JOIN services s ON aps.service_id = s.id
        JOIN doctors d ON s.doctor_id = d.id
        WHERE aps.appointment_id = ?
        ORDER BY s.name
    ''', (appointment_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_total_appointment_cost(appointment_id):
    """Получить общую стоимость приема"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COALESCE(SUM(price), 0)
        FROM appointment_services
        WHERE appointment_id = ?
    ''', (appointment_id,))
    
    total = cursor.fetchone()[0]
    conn.close()
    
    return total

def create_appointment(client_id, doctor_id, service_id, appointment_date, appointment_time, notes=None, source='Повторное посещение', skip_date_validation=False):
    """Создать новый прием с проверкой конфликтов времени
    
    Args:
        source: Источник пациента (откуда узнал о клинике)
        skip_date_validation: Пропустить валидацию даты (для импорта исторических данных)
    """
    try:
        # Валидация даты
        if isinstance(appointment_date, str):
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        elif not skip_date_validation:
            appointment_date = validate_date(appointment_date)
        # Валидация заметок
        notes = validate_notes(notes) if notes else None
    except ValidationError as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка валидации: {e}")
        return None
    except Exception as e:
        # Любые другие ошибки валидации
        return None
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        # Конвертируем time в строку для SQLite
        if hasattr(appointment_time, 'strftime'):
            appointment_time_str = appointment_time.strftime('%H:%M:%S')
        else:
            appointment_time_str = str(appointment_time)
        
        # КРИТИЧЕСКИ ВАЖНО: Проверка конфликтов времени
        cursor.execute('''
            SELECT a.id, c.first_name, c.last_name 
            FROM appointments a
            JOIN clients c ON a.client_id = c.id
            WHERE a.doctor_id = ? 
            AND a.appointment_date = ? 
            AND a.appointment_time = ?
            AND a.status NOT IN ('отменен', 'не явился')
        ''', (doctor_id, appointment_date, appointment_time_str))
        
        existing = cursor.fetchone()
        if existing:
            conn.close()
            if hasattr(st, 'error'):
                st.error(f"❌ Врач уже занят в это время! Пациент: {existing[1]} {existing[2]}")
            return None
        
        # Вставляем прием
        cursor.execute('''
            INSERT INTO appointments (client_id, doctor_id, service_id, appointment_date, appointment_time, notes, source)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (client_id, doctor_id, service_id, appointment_date, appointment_time_str, notes, source))
        
        appointment_id = cursor.lastrowid
        
        # КРИТИЧЕСКИ ВАЖНО: Автоматически добавляем первую услугу в appointment_services
        if service_id:  # Только если service_id был предоставлен
            cursor.execute('SELECT price FROM services WHERE id = ?', (service_id,))
            service = cursor.fetchone()
            if service:
                cursor.execute('''
                    INSERT INTO appointment_services (appointment_id, service_id, price)
                    VALUES (?, ?, ?)
                ''', (appointment_id, service_id, service[0]))
        
        conn.commit()
        conn.close()
        
        return appointment_id
    except sqlite3.IntegrityError as e:
        conn.close()
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка целостности данных: {e}")
        return None
    except sqlite3.Error as e:
        conn.close()
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка создания приема: {e}")
        return None

def get_appointment_by_id(appointment_id):
    """Получить прием по ID"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT a.id, a.client_id, a.doctor_id, a.service_id, a.appointment_date, 
               a.appointment_time, a.status, a.notes, a.start_time, a.end_time,
               c.first_name, c.last_name, c.phone,
               d.first_name, d.last_name, d.specialization,
               s.name, s.price, s.duration_minutes
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN services s ON a.service_id = s.id
        WHERE a.id = ?
    ''', (appointment_id,))
    
    result = cursor.fetchone()
    conn.close()
    
    return result

def update_appointment_status(appointment_id, status, start_time=None, end_time=None):
    """Обновить статус приема"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Вычисляем длительность приема если есть start_time и end_time
    actual_duration = None
    if start_time and end_time:
        start_dt = datetime.fromisoformat(start_time)
        end_dt = datetime.fromisoformat(end_time)
        actual_duration = int((end_dt - start_dt).total_seconds() / 60)
    
    cursor.execute('''
        UPDATE appointments 
        SET status = ?, start_time = ?, end_time = ?, actual_duration_minutes = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
    ''', (status, start_time, end_time, actual_duration, appointment_id))
    
    conn.commit()
    conn.close()

def get_appointments_by_date_range(start_date, end_date, doctor_id=None):
    """Получить приемы по диапазону дат"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Конвертируем даты в строки для SQLite
    if hasattr(start_date, 'strftime'):
        start_date_str = start_date.strftime('%Y-%m-%d')
    else:
        start_date_str = str(start_date)
    
    if hasattr(end_date, 'strftime'):
        end_date_str = end_date.strftime('%Y-%m-%d')
    else:
        end_date_str = str(end_date)
    
    query = '''
        SELECT a.id, a.client_id, a.doctor_id, a.service_id, a.appointment_date, 
               a.appointment_time, a.status, a.notes, a.start_time, a.end_time,
               c.first_name, c.last_name, c.phone,
               d.first_name, d.last_name, d.specialization,
               s.name, s.price, s.duration_minutes
        FROM appointments a
        JOIN clients c ON a.client_id = c.id
        JOIN doctors d ON a.doctor_id = d.id
        JOIN services s ON a.service_id = s.id
        WHERE a.appointment_date BETWEEN ? AND ?
    '''
    
    params = [start_date_str, end_date_str]
    
    if doctor_id:
        query += ' AND a.doctor_id = ?'
        params.append(doctor_id)
    
    query += ' ORDER BY a.appointment_date, a.appointment_time'
    
    cursor.execute(query, params)
    results = cursor.fetchall()
    conn.close()
    
    return results

def delete_appointment(appointment_id):
    """Удалить прием"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Сначала получаем информацию о приеме для логирования
    cursor.execute('SELECT * FROM appointments WHERE id = ?', (appointment_id,))
    appointment = cursor.fetchone()
    
    if appointment:
        # Удаляем прием
        cursor.execute('DELETE FROM appointments WHERE id = ?', (appointment_id,))
        conn.commit()
        conn.close()
        return True
    else:
        conn.close()
        return False

def log_audit_action(user_id, action, table_name=None, record_id=None, old_values=None, new_values=None):
    """Логирование действий пользователя с детальной информацией"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Конвертируем словари в JSON если нужно
        if isinstance(old_values, dict):
            old_values = json.dumps(old_values, ensure_ascii=False)
        if isinstance(new_values, dict):
            new_values = json.dumps(new_values, ensure_ascii=False)
        
        cursor.execute('''
            INSERT INTO audit_log (user_id, action, table_name, record_id, old_values, new_values)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, action, table_name, record_id, old_values, new_values))
        
        conn.commit()
        conn.close()
    except Exception as e:
        # Логирование не должно ломать основную функциональность
        print(f"Ошибка логирования: {e}")

def add_payment_to_service(appointment_service_id, payment_method, amount):
    """Добавить оплату к услуге приема (v2.7)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO appointment_service_payments (appointment_service_id, payment_method, amount)
            VALUES (?, ?, ?)
        ''', (appointment_service_id, payment_method, amount))
        
        conn.commit()
        payment_id = cursor.lastrowid
        conn.close()
        
        return payment_id
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка добавления оплаты: {e}")
        return None

def get_service_payments(appointment_service_id):
    """Получить все оплаты для конкретной услуги приема"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, payment_method, amount, created_at
        FROM appointment_service_payments
        WHERE appointment_service_id = ?
        ORDER BY created_at
    ''', (appointment_service_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def get_appointment_payments_summary(appointment_id):
    """Получить сводку по всем оплатам приема"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            asp.payment_method,
            SUM(asp.amount) as total_amount
        FROM appointment_service_payments asp
        JOIN appointment_services asrv ON asp.appointment_service_id = asrv.id
        WHERE asrv.appointment_id = ?
        GROUP BY asp.payment_method
    ''', (appointment_id,))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def update_appointment_payment_status(appointment_id, total_paid, total_cost):
    """Обновить статус оплаты приема"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Определяем статус оплаты
        if total_paid == 0:
            payment_status = 'не оплачено'
        elif total_paid >= total_cost:
            payment_status = 'оплачено'
        else:
            payment_status = 'частично оплачено'
        
        cursor.execute('''
            UPDATE appointments 
            SET payment_status = ?
            WHERE id = ?
        ''', (payment_status, appointment_id))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка обновления статуса оплаты: {e}")
        return False

def delete_service_payment(payment_id):
    """Удалить оплату"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM appointment_service_payments WHERE id = ?', (payment_id,))
        
        conn.commit()
        conn.close()
        
        return True
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка удаления оплаты: {e}")
        return False

# ==================== УПРАВЛЕНИЕ ПОЛЬЗОВАТЕЛЯМИ ====================

def get_all_users():
    """Получить всех пользователей системы"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, username, access_level, created_at, last_login
            FROM users 
            ORDER BY created_at DESC
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        return users
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка получения пользователей: {e}")
        return []

def create_user(username, password, access_level, name=None):
    """Создать нового пользователя"""
    try:
        import bcrypt
        
        # Хешируем пароль
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Если имя не указано, используем username
        if name is None:
            name = username
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, не существует ли пользователь
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return False, "Пользователь с таким именем уже существует"
        
        # Создаем пользователя
        cursor.execute('''
            INSERT INTO users (username, password_hash, name, access_level, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        ''', (username, hashed_password, name, access_level))
        
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        
        return True, f"Пользователь {username} успешно создан (ID: {user_id})"
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка создания пользователя: {e}")
        return False, f"Ошибка создания пользователя: {e}"

def update_user_password(username, new_password):
    """Обновить пароль пользователя"""
    try:
        import bcrypt
        
        # Хешируем новый пароль
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if not cursor.fetchone():
            conn.close()
            return False, "Пользователь не найден"
        
        # Обновляем пароль
        cursor.execute('''
            UPDATE users 
            SET password_hash = ?, updated_at = datetime('now')
            WHERE username = ?
        ''', (hashed_password, username))
        
        conn.commit()
        conn.close()
        
        return True, f"Пароль пользователя {username} успешно обновлен"
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка обновления пароля: {e}")
        return False, f"Ошибка обновления пароля: {e}"

def update_user_access_level(username, new_access_level):
    """Обновить уровень доступа пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if not cursor.fetchone():
            conn.close()
            return False, "Пользователь не найден"
        
        # Обновляем уровень доступа
        cursor.execute('''
            UPDATE users 
            SET access_level = ?, updated_at = datetime('now')
            WHERE username = ?
        ''', (new_access_level, username))
        
        conn.commit()
        conn.close()
        
        return True, f"Уровень доступа пользователя {username} обновлен на {new_access_level}"
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка обновления уровня доступа: {e}")
        return False, f"Ошибка обновления уровня доступа: {e}"

def delete_user(username):
    """Удалить пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        if not user:
            conn.close()
            return False, "Пользователь не найден"
        
        # Нельзя удалить последнего владельца
        cursor.execute('SELECT COUNT(*) FROM users WHERE access_level = "owner"', ())
        owner_count = cursor.fetchone()[0]
        
        if user[0] == 1 and owner_count == 1:  # Предполагаем, что ID 1 - это владелец
            conn.close()
            return False, "Нельзя удалить последнего владельца системы"
        
        # Удаляем пользователя
        cursor.execute('DELETE FROM users WHERE username = ?', (username,))
        
        conn.commit()
        conn.close()
        
        return True, f"Пользователь {username} успешно удален"
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка удаления пользователя: {e}")
        return False, f"Ошибка удаления пользователя: {e}"

def reset_user_password(username):
    """Сбросить пароль пользователя на временный"""
    try:
        import secrets
        import string
        
        # Генерируем временный пароль
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Обновляем пароль
        success, message = update_user_password(username, temp_password)
        
        if success:
            return True, f"Пароль пользователя {username} сброшен. Новый временный пароль: {temp_password}"
        else:
            return False, message
    except Exception as e:
        if hasattr(st, 'error'):
            st.error(f"❌ Ошибка сброса пароля: {e}")
        return False, f"Ошибка сброса пароля: {e}"

if __name__ == "__main__":
    # Инициализация базы данных
    init_database_v2()
    create_default_users()
    create_default_data()
    print("✅ База данных версии 2.0 создана и заполнена тестовыми данными!")
