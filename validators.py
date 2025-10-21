#!/usr/bin/env python3
"""
Модуль валидации данных для повышения безопасности
"""

import re
from datetime import date, timedelta

class ValidationError(Exception):
    """Кастомное исключение для ошибок валидации"""
    pass

def validate_search_query(query):
    """Валидация поискового запроса для защиты от SQL injection"""
    if not query:
        raise ValidationError("Поисковый запрос не может быть пустым")
    
    # Минимальная длина
    query = query.strip()
    if len(query) < 2:
        raise ValidationError("Поисковый запрос должен содержать минимум 2 символа")
    
    # Максимальная длина
    if len(query) > 100:
        raise ValidationError("Поисковый запрос слишком длинный")
    
    # Проверка на SQL-инъекции
    dangerous_patterns = ['--', ';', '/*', '*/', 'xp_', 'sp_', 'DROP', 'DELETE', 'INSERT', 'UPDATE', 'CREATE', 'ALTER']
    query_upper = query.upper()
    
    for pattern in dangerous_patterns:
        if pattern.upper() in query_upper:
            raise ValidationError("Недопустимые символы в поисковом запросе")
    
    return query

def validate_phone(phone):
    """Валидация телефонного номера (казахстанский формат)"""
    if not phone:
        raise ValidationError("Телефон обязателен для заполнения")
    
    # Удаляем пробелы и дефисы
    phone_clean = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    
    # Казахстанский формат: +7XXXXXXXXXX или 8XXXXXXXXXX
    pattern_plus7 = r'^\+7\d{10}$'
    pattern_8 = r'^8\d{10}$'
    
    if not (re.match(pattern_plus7, phone_clean) or re.match(pattern_8, phone_clean)):
        raise ValidationError("Неверный формат телефона. Используйте: +7XXXXXXXXXX")
    
    # Конвертируем 8 в +7
    if phone_clean.startswith('8'):
        phone_clean = '+7' + phone_clean[1:]
    
    return phone_clean

def validate_email(email):
    """Валидация email адреса"""
    if not email:
        return None  # Email необязателен
    
    email = email.strip()
    
    if len(email) > 254:
        raise ValidationError("Email слишком длинный")
    
    # Базовая проверка формата email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(pattern, email):
        raise ValidationError("Неверный формат email")
    
    return email.lower()

def validate_date(appointment_date):
    """Валидация даты приема"""
    if not appointment_date:
        raise ValidationError("Дата приема обязательна")
    
    # Конвертируем в date если это строка
    if isinstance(appointment_date, str):
        from datetime import datetime
        try:
            appointment_date = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        except ValueError:
            raise ValidationError("Неверный формат даты. Используйте: YYYY-MM-DD")
    
    today = date.today()
    max_future = today + timedelta(days=365)
    
    # Проверяем, что дата не в прошлом
    if appointment_date < today:
        raise ValidationError("Нельзя создать прием в прошлом")
    
    # Проверяем, что дата не слишком далеко в будущем
    if appointment_date > max_future:
        raise ValidationError("Нельзя создать прием более чем на год вперед")
    
    return appointment_date

def validate_name(name, field_name="Имя"):
    """Валидация имени/фамилии"""
    if not name:
        raise ValidationError(f"{field_name} обязательно для заполнения")
    
    name = name.strip()
    
    if len(name) < 2:
        raise ValidationError(f"{field_name} должно содержать минимум 2 символа")
    
    if len(name) > 50:
        raise ValidationError(f"{field_name} слишком длинное")
    
    # Проверяем, что содержит только буквы, пробелы и дефисы
    if not re.match(r'^[а-яА-ЯёЁa-zA-Z\s\-]+$', name):
        raise ValidationError(f"{field_name} должно содержать только буквы")
    
    return name

def validate_notes(notes):
    """Валидация заметок"""
    if not notes:
        return None
    
    notes = notes.strip()
    
    if len(notes) > 500:
        raise ValidationError("Заметки слишком длинные (максимум 500 символов)")
    
    # Проверяем на опасные символы
    dangerous_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
    notes_lower = notes.lower()
    
    for pattern in dangerous_patterns:
        if pattern in notes_lower:
            raise ValidationError("Недопустимые символы в заметках")
    
    return notes

def sanitize_input(input_str):
    """Общая санитизация входных данных"""
    if not input_str:
        return input_str
    
    # Удаляем лишние пробелы
    input_str = input_str.strip()
    
    # Удаляем потенциально опасные символы
    dangerous_chars = ['<', '>', '&', '"', "'"]
    for char in dangerous_chars:
        if char in input_str:
            input_str = input_str.replace(char, '')
    
    return input_str

