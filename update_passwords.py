#!/usr/bin/env python3
"""
Скрипт для обновления паролей существующих пользователей в базе данных
"""

import sqlite3
import bcrypt
import os

# Пароли из production_passwords.txt
OWNER_PASSWORD = "OKZQ%aFv&UXpjeDMu%ZU6Ic!"
ADMIN_PASSWORD = "4HDEO!Q5%TW%h&pcTiqOIky9"
CRM_PASSWORD = "$Uv68@a$Gb1d2#hgKb#n5ggr"

def update_user_passwords():
    """Обновить пароли всех пользователей в базе данных"""
    print("=" * 80)
    print("🔐 ОБНОВЛЕНИЕ ПАРОЛЕЙ ПОЛЬЗОВАТЕЛЕЙ")
    print("=" * 80)
    
    # Подключение к базе данных
    conn = sqlite3.connect('medical_center.db')
    cursor = conn.cursor()
    
    # Список пользователей для обновления
    users_to_update = [
        ('owner', OWNER_PASSWORD, 'Владелец системы'),
        ('admin', ADMIN_PASSWORD, 'Администратор'),
        ('crm_user', CRM_PASSWORD, 'CRM Пользователь'),
    ]
    
    updated_count = 0
    
    for username, password, name in users_to_update:
        # Проверяем, существует ли пользователь
        cursor.execute('SELECT id, username FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        
        if user:
            # Хешируем новый пароль
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # Обновляем пароль
            cursor.execute('''
                UPDATE users 
                SET password_hash = ?, updated_at = datetime('now')
                WHERE username = ?
            ''', (password_hash, username))
            
            print(f"✅ Обновлен пароль для пользователя: {username} ({name})")
            updated_count += 1
        else:
            # Если пользователь не существует, создаем его
            salt = bcrypt.gensalt()
            password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
            
            # Определяем уровень доступа
            if username == 'owner':
                access_level = 'owner'
            elif username == 'admin':
                access_level = 'admin'
            else:
                access_level = 'crm'
            
            cursor.execute('''
                INSERT INTO users (username, password_hash, name, access_level, created_at)
                VALUES (?, ?, ?, ?, datetime('now'))
            ''', (username, password_hash, name, access_level))
            
            print(f"✅ Создан новый пользователь: {username} ({name})")
            updated_count += 1
    
    # Сохраняем изменения
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 80)
    print(f"✅ Успешно обновлено/создано пользователей: {updated_count}")
    print("=" * 80)
    print("\n📋 Обновленные пароли:")
    print(f"   owner: {OWNER_PASSWORD}")
    print(f"   admin: {ADMIN_PASSWORD}")
    print(f"   crm_user: {CRM_PASSWORD}")
    print("\n⚠️  Сохраните эти пароли в безопасном месте!")
    print("=" * 80)

if __name__ == "__main__":
    try:
        update_user_passwords()
    except Exception as e:
        print(f"\n❌ Ошибка при обновлении паролей: {e}")
        import traceback
        traceback.print_exc()

