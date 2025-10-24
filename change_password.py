"""
Модуль для смены пароля пользователя
"""

import streamlit as st
from database import update_user_password, get_connection
import bcrypt

def show_change_password_form():
    """Показать форму смены пароля"""
    st.subheader("Смена пароля")
    
    with st.form("change_password_form"):
        current_password = st.text_input(
            "Текущий пароль",
            type="password",
            help="Введите ваш текущий пароль"
        )
        
        new_password = st.text_input(
            "Новый пароль",
            type="password",
            help="Минимум 8 символов"
        )
        
        confirm_password = st.text_input(
            "Подтвердите новый пароль",
            type="password",
            help="Повторите новый пароль"
        )
        
        if st.form_submit_button("Изменить пароль", use_container_width=True):
            if not current_password or not new_password or not confirm_password:
                st.error("Заполните все поля")
            elif new_password != confirm_password:
                st.error("Новые пароли не совпадают")
            elif len(new_password) < 8:
                st.error("Пароль должен содержать минимум 8 символов")
            else:
                # Проверяем текущий пароль
                username = st.session_state.get('username', '')
                if verify_current_password(username, current_password):
                    # Обновляем пароль
                    success, message = update_user_password(username, new_password)
                    if success:
                        st.success("Пароль успешно изменен!")
                        # Логируем действие
                        from database import log_audit_action
                        log_audit_action(
                            st.session_state.get('user_id', 0),
                            'PASSWORD_CHANGE',
                            'user',
                            st.session_state.get('user_id', 0),
                            'password_changed',
                            'password_updated'
                        )
                    else:
                        st.error(f"Ошибка изменения пароля: {message}")
                else:
                    st.error("Неверный текущий пароль")

def verify_current_password(username, password):
    """Проверить текущий пароль пользователя"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT password_hash FROM users WHERE username = ?
        ''', (username,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            stored_hash = result[0]
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
        
        return False
    except Exception as e:
        st.error(f"Ошибка проверки пароля: {e}")
        return False

def main():
    """Главная функция модуля смены пароля"""
    st.title("Смена пароля")
    
    # Проверяем аутентификацию
    if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
        st.error("Необходимо войти в систему")
        return
    
    # Показываем информацию о пользователе
    username = st.session_state.get('username', '')
    name = st.session_state.get('name', '')
    
    st.info(f"Пользователь: {name} ({username})")
    
    # Показываем форму смены пароля
    show_change_password_form()
    
    # Кнопка возврата
    if st.button("Назад", use_container_width=True):
        st.session_state['current_page'] = 'main'
        st.rerun()

if __name__ == "__main__":
    main()
