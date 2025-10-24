#!/usr/bin/env python3
"""
Модуль аутентификации для версии 2.0
"""

import streamlit as st
import bcrypt
from datetime import datetime, timedelta
from database import get_connection, log_audit_action

def login_page():
    """Страница входа в систему с rate limiting"""
    st.title("🏥 Медицинский Центр - Вход в систему")
    st.warning("⚠️ **Внимание:** Не обновляйте страницу (F5) после входа - это сбросит сессию. Используйте кнопки навигации внутри системы.")
    st.markdown("---")
    
    # Инициализация счетчиков неудачных попыток
    if 'failed_attempts' not in st.session_state:
        st.session_state['failed_attempts'] = 0
        st.session_state['lockout_until'] = None
        st.session_state['last_attempt_time'] = None
    
    # Проверка блокировки
    if st.session_state['lockout_until']:
        if datetime.now() < st.session_state['lockout_until']:
            remaining = (st.session_state['lockout_until'] - datetime.now()).seconds // 60
            st.error(f"🔒 Слишком много неудачных попыток входа. Попробуйте через {remaining + 1} минут.")
            return
        else:
            # Разблокировка
            st.session_state['failed_attempts'] = 0
            st.session_state['lockout_until'] = None
    
    # Центрируем форму входа (27% ширины)
    col1, col2, col3 = st.columns([36.5, 27, 36.5])
    
    with col2:
        with st.form("login_form"):
            st.subheader("🔐 Вход в систему")
            
            username = st.text_input("👤 Имя пользователя:", key="login_username")
            password = st.text_input("🔒 Пароль:", type="password", key="login_password")
            
            col_btn1, col_btn2 = st.columns([1, 1])
            with col_btn1:
                login_button = st.form_submit_button("🚀 Войти", use_container_width=True)
            with col_btn2:
                if st.form_submit_button("🔄 Обновить", use_container_width=True):
                    st.rerun()
            
            if login_button:
                if not username or not password:
                    st.error("❌ Пожалуйста, заполните все поля")
                elif authenticate_user(username, password):
                    # Успешный вход - сбрасываем счетчик
                    st.session_state['failed_attempts'] = 0
                    st.session_state['lockout_until'] = None
                    st.success("✅ Успешный вход в систему!")
                    st.rerun()
                else:
                    # Неудачная попытка
                    st.session_state['failed_attempts'] += 1
                    st.session_state['last_attempt_time'] = datetime.now()
                    
                    # Показываем понятное сообщение об ошибке
                    st.error("❌ Неверное имя пользователя или пароль")
                    
                    # Блокировка после 5 неудачных попыток
                    if st.session_state['failed_attempts'] >= 5:
                        st.session_state['lockout_until'] = datetime.now() + timedelta(minutes=15)
                        st.error("🔒 Превышено количество попыток входа. Доступ заблокирован на 15 минут.")
                    else:
                        remaining_attempts = 5 - st.session_state['failed_attempts']
                        st.error(f"❌ Неверное имя пользователя или пароль. Осталось попыток: {remaining_attempts}")

def authenticate_user(username, password):
    """Аутентификация пользователя"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, password_hash, name, access_level
        FROM users
        WHERE username = ?
    ''', (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and user[2] and bcrypt.checkpw(password.encode('utf-8'), user[2].encode('utf-8')):
        # Сохраняем данные пользователя в session_state
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user[0]
        st.session_state['username'] = user[1]
        st.session_state['name'] = user[3]
        st.session_state['access_level'] = user[4]
        
        # Логируем вход
        log_audit_action(user[0], 'LOGIN', 'users', user[0])
        
        return True
    
    return False

def logout():
    """Выход из системы"""
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        # Логируем выход
        log_audit_action(st.session_state.get('user_id'), 'LOGOUT', 'users', st.session_state.get('user_id'))
    
    # Очищаем session_state
    keys_to_remove = ['authenticated', 'user_id', 'username', 'name', 'access_level']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]
    
    st.rerun()

def check_access(required_access_level):
    """Проверка уровня доступа"""
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        return False
    
    user_access_level = st.session_state.get('access_level', '')
    
    # Owner имеет доступ ко всему
    if user_access_level == 'owner':
        return True
    
    # Admin имеет доступ ко всему
    if user_access_level == 'admin':
        return True
    
    # Проверяем требуемый уровень доступа
    if required_access_level == 'admin' and user_access_level not in ['admin', 'owner']:
        return False
    elif required_access_level == 'crm' and user_access_level not in ['admin', 'crm', 'owner']:
        return False
    
    return True

def show_user_info():
    """Показать информацию о пользователе в сайдбаре"""
    if 'authenticated' in st.session_state and st.session_state['authenticated']:
        with st.sidebar:
            st.markdown("---")
            st.markdown(f"**Пользователь:** {st.session_state['name']}")
            st.markdown(f"**Уровень доступа:** {st.session_state['access_level']}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Смена пароля", key="change_password_button"):
                    st.session_state['show_change_password'] = True
                    st.rerun()
            
            with col2:
                if st.button("Выход", key="logout_button_v2"):
                    logout()

def get_status_color(status):
    """Получить цвет для статуса приема"""
    colors = {
        'записан': '#808080',      # Серая рамка
        'на приеме': '#FFD700',    # Желтая рамка
        'прием завершен': '#00FF00', # Ярко зеленая рамка
        'не явился': '#FF00FF'     # Кислотно фиолетовая рамка
    }
    return colors.get(status, '#808080')

def get_status_emoji(status):
    """Получить эмодзи для статуса приема"""
    emojis = {
        'записан': '📅',
        'на приеме': '🔄',
        'прием завершен': '✅',
        'не явился': '❌'
    }
    return emojis.get(status, '📅')
